import copy
import datetime
import os
import pickle
import pickletools
import platform
from functools import partial
from typing import Tuple

import fitz
import graphviz

from PyQt6.QtCore import (QDate, QFile, QLocale, QPoint, QRegularExpression,
                          Qt, QTimer, QVariant, pyqtSignal)
from PyQt6.QtGui import (QAction, QCloseEvent, QColor, QCursor, QIcon, QImage,
                         QPainter, QPen, QPixmap, QRegularExpressionValidator,
                         QWheelEvent)
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import (QApplication, QCalendarWidget, QDialog,
                             QDialogButtonBox, QFileDialog, QGraphicsScene,
                             QGraphicsView, QHBoxLayout, QInputDialog, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QMessageBox, QPushButton,
                             QScrollArea, QSlider, QTabBar, QToolBar,
                             QVBoxLayout, QWidget, QColorDialog)
from win32 import win32api, win32print

from Archivo import *
from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Persona import *
from Informes import *

class GraficoOrganigramaView(QGraphicsView):
    """Un QGraphicsView que contiene la visualizacion del arbol del organigrama"""
    
    def __init__(self, archivo: Archivo, raiz: NodoArbol):
        super().__init__()
        self.archivo = archivo
        self.raiz = raiz
        
        self.colorRellenoNodo = 'white'
        self.colorBordeNodo =   'black'
        self.colorTextoNodo =   'black'
        self.colorLineas = 'black'
        
        # Crear la escena y opciones de renderizado y de barra de scroll
        self.setScene(QGraphicsScene())
        self.setRenderHint(QPainter.RenderHint.Antialiasing)    
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Dibujar el arbol de organigrama y centrarlo
        self.dibujarArbolOrganigrama()
        self.redimensionarGrafico()
        # Guardar la dimension actual del widget
        self.dim_anterior = self.size()
        
    def paintEvent(self, event):
        """Evento que se llama cada vez que se dibuja el elemento en la interfaz"""
        super().paintEvent(event)
        # Redimensionar y central el organigrama si el tamaño dibujado es distinto al anterior.
        # (Es decir, cuando se cambio el tamaño de la ventana)
        if self.size() != self.dim_anterior:
            self.redimensionarGrafico()
            self.dim_anterior = self.size()
        
    def redimensionarGrafico(self):
        """Ajustar la vista de la escena al tamaño actual de esta en la ventana de la aplicacion"""
        rectangulo_scene = self.scene().itemsBoundingRect()
        margen_x, margen_y = 20, 20 # Mantener un margen para no dibujar al borde de la aplicacion
        rectangulo_ajustado = rectangulo_scene.adjusted(-margen_x, -margen_y, margen_x, margen_y)
        self.fitInView(rectangulo_ajustado, Qt.AspectRatioMode.KeepAspectRatio)

    def dibujarArbolOrganigramaAPdf(self, raiz: NodoArbol, file_path: str) -> str:
        """Dibuja el grafo con GraphViz y lo renderiza a un archivo pdf, retornando la ruta de este archivo"""
        
        # Generar el grafo con GraphViz
        dot = graphviz.Digraph(format='pdf')
        self.dibujarNodos(dot, raiz)
        
        # Definir atributos del archivo DOT a renderizar
        dot.graph_attr.update(
            splines='ortho',    # Dibujar lineas ortogonalmente
            rankdir='TB',       # Orientacion Vertical (Top to Bottom)
            fontname='helvetica')
            
        dot.render(filename=file_path, cleanup=True)
        return file_path + ".pdf"

    def dibujarArbolOrganigrama(self):
        """Dibuja el grafo con GraphViz y lo renderiza a la vista de la escena"""

        # Borrar el contenido actual de la escena visualizada
        self.scene().clear() 

        if self.archivo is None:
            return

        # Generar el grafo con GraphViz
        dot = graphviz.Digraph(format='svg')
        self.dibujarNodos(dot, self.raiz)

        # Definir atributos del lenguaje DOT a renderizar
        dot.graph_attr.update(
            splines='ortho',    # Dibujar lineas ortogonalmente
            rankdir='TB',       # Orientacion Vertical (Top to Bottom)
            fontname='helvetica')
    
        # Renderizar el grafo como SVG y dibujarlo en la QGraphicsScene del widget
        svgItem = QGraphicsSvgItem()
        svgRenderer = QSvgRenderer(dot.pipe())
        svgItem.setSharedRenderer(svgRenderer)
        self.scene().addItem(svgItem)
        
    def dibujarNodos(self, dot: graphviz.Digraph, nodo: NodoArbol):
        """Agregar recursivamente los elementos a dibujar de los nodos al objeto dot de GraphViz"""
        
        if nodo is None:
            return

        # Si el nodo tiene un responsable (jefe) obtener el objeto persona del jefe
        jefe = None
        if nodo.dep is not None:
            jefe: Persona = self.archivo.personasPorCodigo.get(nodo.dep.codigoResponsable)

        # Crear el texto de nodo con el nombre de la dependencia y el nombre de jefe si es que existe.
        # Se utiliza el formato del lenguaje DOT de graphviz para formatear el texto del nodo
        textoNodo = f'<<FONT POINT-SIZE="14">{nodo.dep}   </FONT>'
        if jefe is not None:
            textoNodo += f'<BR/><FONT POINT-SIZE="8">{jefe.nombre}, {jefe.apellido}  </FONT>'
        textoNodo += '>'
        
        # Agregar el nodo con forma rectangular, centrar el texto
        dot.node(str(id(nodo)), label=textoNodo, shape="rectangle", labeljust="c", 
                 style="filled", color=self.colorBordeNodo, fillcolor=self.colorRellenoNodo, fontcolor=self.colorTextoNodo)

        # Recursivamente dibujamos nodos por cada nodo hijo
        for hijo in nodo.hijos:
            self.dibujarNodos(dot, hijo)

            # Agregamos la conexion entre el nodo padre y el nodo hijo
            dot.edge(str(id(nodo)), str(id(hijo)), arrowhead='none', arrowtail='none', dir='none', color=self.colorLineas)
              
class GraficoOrganigramaWidget(QWidget):
    """Widget que contiene un OrganizationalChartView del archivo, se utilizara como widget central del programa"""
    
    def __init__(self, archivo: Archivo, raiz: NodoArbol):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.archivo = archivo
        self.raiz = raiz
        self.graficoOrganigrama = GraficoOrganigramaView(archivo, raiz)
        self.layout.addWidget(self.graficoOrganigrama)

class ZoomWidget(QWidget):
    """Widget que controla la escala (zoom) de una vista con una barra para asignar el factor de escala"""
    def __init__(self, vistaDestino: QGraphicsView, zoomMinimo: int = 10, zoomMaximo: int = 999, parent=None):
        super().__init__(parent)
        self.vistaDestino = vistaDestino
        """La vista que se va escalar por el factor de escala seleccionado por el ZoomWidget"""
        self.zoomMinimo = zoomMinimo
        self.zoomMaximo = zoomMaximo
        self.crearElementos()

    def crearElementos(self):
        """Crear los elementos visuales y funcionales que perteneceran al ZoomWidget"""
        
        # Creamos un Deslizador para mostrar y editar el valor de zoom
        self.sliderZoom = QSlider(Qt.Orientation.Horizontal)
        self.sliderZoom.setMinimum(self.zoomMinimo)
        self.sliderZoom.setMaximum(self.zoomMaximo)
        self.zoomMedio = (self.zoomMinimo + self.zoomMaximo) / 2
        self.sliderZoom.setSliderPosition(int(self.zoomMedio))
        self.sliderZoom.setTickPosition(QSlider.TickPosition.NoTicks)
        self.sliderZoom.setMaximumWidth(200) 
        self.sliderZoom.setFixedHeight(20) # Asegurar que el deslizador sea el mismo tamaño que los botones
        # Conectar el evento de cambio de valor de deslizador a la funcion para actualiz
        self.sliderZoom.valueChanged.connect(self.actualizarZoom)
        # Crear un campo de texto que muestre el porcentaje de zoom
        self.porcentajeZoom = QLabel("100%")
        self.porcentajeZoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.porcentajeZoom.setStyleSheet("color: dimgrey; padding-bottom: 3.5px;") # Asignar formato con CSS
        self.porcentajeZoom.setFixedWidth(30)  # Asignar un valor fijo de anchura para el texto que considera el valor maximo de 100%
        
        # Crear un contenedor para crear una disposición horizontal para los botones y el deslizador
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 10, 0)  # Asignar margen a la derecha de 10 pixeles
        layout.setSpacing(0)                    # Establecer el espaciado entre elementos a 0
        layout.addStretch(1)                    # Añadir estiramiento para alinear los elementos a la derecha
      
        # Crear un estilo para los botones de +- zoom
        estiloDeBoton = """
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: center;
                padding-bottom: 3.5px;
                color: dimgrey;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 40);
            }
        """
        # Crear boton para disminuir el valor de zoom
        botonDisminuir = QPushButton("－")
        botonDisminuir.setFixedSize(20, 20)
        botonDisminuir.setStyleSheet(estiloDeBoton)
        botonDisminuir.pressed.connect(partial(self.empezarTimerDeZoom, -10))
        botonDisminuir.released.connect(self.terminarTimerDeZoom)
        botonDisminuir.clicked.connect(partial(self.incrementarZoom, -10))
        # Crear boton para aumentar el valor de zoom
        botonAumentar = QPushButton("＋")
        botonAumentar.setFixedSize(20, 20)
        botonAumentar.setStyleSheet(estiloDeBoton)
        botonAumentar.pressed.connect(partial(self.empezarTimerDeZoom, 10))
        botonAumentar.released.connect(self.terminarTimerDeZoom)
        botonAumentar.clicked.connect(partial(self.incrementarZoom, 10))
        
        # Crear un timer para el aumento gradual del zoom cuando mantenemos presionado uno de los botones
        self.zoomTimer = QTimer()
        self.zoomTimer.setSingleShot(False)
        self.zoomTimer.timeout.connect(self.manejarTemporizadorZoom)

        # Agregar los elementos en orden al layout
        layout.addWidget(botonDisminuir)
        layout.addWidget(self.sliderZoom, 1)
        layout.addWidget(botonAumentar)
        layout.addWidget(self.porcentajeZoom)
        # Establecer la dispocion creada al ZoomWidget
        self.setLayout(layout)
                      
                      
    # Sobreescribir el evento de dibujo para pintar una linea de marca en la mitad del deslizador
    def paintEvent(self, event):
        super().paintEvent(event)  # Llamar primero el evento base de pintado
        
        # Dibujar una linea gris con un ancho de 2 pixeles en el medio del slider de zoom
        painter = QPainter(self)    
        pen = QPen(QColor(215, 215, 215))
        pen.setWidth(2)      
        painter.setPen(pen)
        centroDeSlider = self.sliderZoom.geometry().center()
        painter.drawLine(centroDeSlider.x(), centroDeSlider.y() - 7, 
                         centroDeSlider.x(), centroDeSlider.y() + 7)
        
    def empezarTimerDeZoom(self, step):
        if not self.zoomTimer.isActive():
            self.pasoZoomTimer = step
            self.intervaloZoomTimer = 300  # Ajustar intervalo inicial del timer aqui
            self.zoomTimer.setInterval(self.intervaloZoomTimer)
            self.zoomTimer.start()

    def terminarTimerDeZoom(self):
        if self.zoomTimer.isActive():
            self.zoomTimer.stop()

    def manejarTemporizadorZoom(self):
        if self.zoomTimer.interval() == 300:    # Primera llamada
            self.intervaloZoomTimer = 100       # Ajustar el nuevo intervalo aqui (cuando mantenemos apretado el boton)
        self.incrementarZoom(self.pasoZoomTimer)

    def incrementarZoom(self, paso=None):
        """Funcion que incrementa el valor de zoom con un paso y maneja las escalas del slider"""
        # Cuando estamos manteniendo apretado el boton usar el timer
        if paso is None:
            paso = self.pasoZoomTimer
            
        valorActual = self.sliderZoom.value()
        
        # Mapear el paso con las diferentes escalas lineales con el medio del slider como punto medio
        if valorActual == self.zoomMedio:
            if paso < 0:
                normalizador = (self.zoomMedio - self.zoomMinimo) / (100 - self.zoomMinimo)
            else:
                normalizador = (self.zoomMaximo - self.zoomMedio) / (self.zoomMaximo - 100)
        elif valorActual < self.zoomMedio:
            normalizador = (self.zoomMedio - self.zoomMinimo) / (100 - self.zoomMinimo)
        else:
            normalizador = (self.zoomMaximo - self.zoomMedio) / (self.zoomMaximo - 100) 

        paso = paso * normalizador
        paso = round(paso)
                
        valorNuevo = valorActual + paso
        valorNuevo = max(self.zoomMinimo, min(self.zoomMaximo, valorNuevo))
        self.sliderZoom.setValue(valorNuevo)

        # Ajuste el intervalo del temporizador en función del tiempo que mantenga pulsado el botón
        self.intervaloZoomTimer -= 10
        self.intervaloZoomTimer = max(30, self.intervaloZoomTimer)
        self.zoomTimer.setInterval(self.intervaloZoomTimer)
        
    def actualizarZoom(self, valor):
        """Funcion para actualizar el zoom con el valor deseado"""
        
        # Asignar factor de zoom dependiendo de hacia que lado del valor medio esta (se utilizando dos escalas)               
        if valor <= self.zoomMedio:
            factorZoom = 1.0 - (1.0 - (valor - self.zoomMinimo) / (self.zoomMedio - self.zoomMinimo)) * (1.0 - self.zoomMinimo / 100)
        else:
            factorZoom = 1.0 + (valor - self.zoomMedio) / (self.zoomMaximo - self.zoomMedio) * (self.zoomMaximo / 100 - 1.0)

        # Ajustar cuando el valor se aproxime al 100% del zoom (centro del control deslizante)
        if 0.9 < factorZoom < 1.09:    
            valor = self.zoomMedio
            self.sliderZoom.setSliderPosition(int(self.zoomMedio))
            factorZoom = 1.0
            
        # Actualizar el texto que muestra el porcentaje de zoom
        porcentajeDeZoom = f"{round(factorZoom * 100)}%"
        self.porcentajeZoom.setText(porcentajeDeZoom)
        # Aplicar el la escala del factor de zoom a la vista destino
        self.vistaDestino.resetTransform()
        self.vistaDestino.scale(factorZoom, factorZoom)  
             
    def updateOnScroll(self, event: QWheelEvent):
        """Sobreescribir el evento de utilizar la rueda del mouse"""
        delta = event.angleDelta().y() / 120  # Obtener delta de rueda de desplazamiento
        step = 10  # Ajustar el paso de zoom
        valor = self.sliderZoom.value()
        nuevoValor = max(self.zoomMinimo, min(self.zoomMaximo , valor + (delta * step)))
        self.sliderZoom.setValue(int(nuevoValor))

class EntradaFechaDialog(QDialog):
    """Caja de dialogo que pide una fecha utilizando un calendario"""
    accepted = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar fecha")
        # Crear el widget de calendario para pedir la fecha
        widgetCalendario = QCalendarWidget()
        widgetCalendario.setGridVisible(True)
        widgetCalendario.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        widgetCalendario.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        widgetCalendario.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        widgetCalendario.setLocale(QLocale.system())
        widgetCalendario.setMinimumDate(QDate(1900, 1, 1))
        widgetCalendario.setMaximumDate(QDate(2100, 12, 31))
        widgetCalendario.setSelectedDate(QDate.currentDate())
        layout = QVBoxLayout()
        layout.addWidget(widgetCalendario)
        
        botonDeCaja = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botonDeCaja.accepted.connect(self.accept)
        botonDeCaja.rejected.connect(self.reject)
        layout.addWidget(botonDeCaja)
        
        self.setLayout(layout)
        
        self.widgetCalendario = widgetCalendario
        
    def accept(self):
        self.accepted.emit()  # Emit the accepted signal
        super().accept()  # Call the base accept method to close the dialog
   
    def obtenerFecha(self):
        return self.widgetCalendario.selectedDate().toPyDate()

class SelecionDeDependenciaDialog(QDialog):
    """Caja de dialogo que pide selecionar una dependencia del arbol"""

    NodoArbolRole = Qt.ItemDataRole.UserRole + 1  # Rol propio para almacenar el objeto nodoArbol
    
    def __init__(self, nodoRaiz: NodoArbol, nodosAExcluir: list[NodoArbol] = [], titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(250)
        self.layout = QVBoxLayout()

        self.widgetLista = QListWidget()
        self.popularLista(nodoRaiz, nodosAExcluir)
        self.layout.addWidget(self.widgetLista)

        self.boton = QPushButton("Seleccionar")
        self.boton.clicked.connect(self.accept)
        self.layout.addWidget(self.boton)

        self.setLayout(self.layout)

    def popularLista(self, nodo: NodoArbol, nodosAExcluir: list[NodoArbol]):
        if nodo not in nodosAExcluir:
            itemDeLista = QListWidgetItem(nodo.dep.nombre)
            itemDeLista.setData(self.NodoArbolRole, nodo)  # Set the node reference as data
            self.widgetLista.addItem(itemDeLista)
            for child in nodo.hijos:
                self.popularLista(child, nodosAExcluir)

    def nodoSeleccionado(self) -> NodoArbol:
        itemSeleccionado = self.widgetLista.currentItem()
        return itemSeleccionado.data(self.NodoArbolRole)

class DatosPersonaDialog(QDialog):
    """Caja de dialogo que pide selecionar una dependencia del arbol"""
    
    def __init__(self, persona: Persona = None, titulo = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.layout = QVBoxLayout(self)
        
        self.inputs: dict[str, QLineEdit] = {}
        self.errorLabels: dict[str, QLabel] = {}

        for propiedad, (regex, mensajeError) in PersonaRegex.patrones.items():
            if propiedad == "codigo" or propiedad == "dependencia":
                continue

            label = QLabel(propiedad.capitalize() + ":")
            self.layout.addWidget(label)

            campoDeEntrada = QLineEdit()
            self.layout.addWidget(campoDeEntrada)
            self.inputs[propiedad] = campoDeEntrada

            validator = QRegularExpressionValidator(QRegularExpression(regex), self)
            campoDeEntrada.setValidator(validator)

            errorLabel = QLabel(self)
            errorLabel.setStyleSheet("color: red")
            errorLabel.setText(mensajeError)
            errorLabel.setVisible(False)
            self.layout.addWidget(errorLabel)
            self.errorLabels[propiedad] = errorLabel

            def actualizarErrorLabel():
                campoDeEntrada: QLineEdit = self.sender()
                propiedad = next(key for key, value in self.inputs.items() if value is campoDeEntrada)
                errorLabel = self.errorLabels[propiedad]
                if campoDeEntrada.hasAcceptableInput():
                    errorLabel.setVisible(False)
                else:
                    errorLabel.setVisible(True)

            campoDeEntrada.inputRejected.connect(actualizarErrorLabel)
            campoDeEntrada.textChanged.connect(actualizarErrorLabel)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        if persona is not None:
            self.llenarCamposDeEntrada(persona)

    def llenarCamposDeEntrada(self, persona: Persona):
        """Llenar los campos de entrada con los valores que tiene persona"""
        for prop, campoDeEntrada in self.inputs.items():
            if hasattr(persona, prop):
                value = getattr(persona, prop)
                if value is not None:
                    campoDeEntrada.setText(str(value))
                
    def obtenerPersona(self):
            datosPersona = {}
            for propiedad, campoDeEntrada in self.inputs.items():
                valor = campoDeEntrada.text()
                if propiedad == "salario":
                    if valor == "":
                        valor = 0
                    else:
                        valor = int(valor)  # Convertir entrada de salario a entero
                datosPersona[propiedad] = valor

            persona = Persona(**datosPersona) # Pasar todas las propiedades como argumento de constructor
            return persona
 
class PersonaSelectionDialog(QDialog):
    """Caja de dialogo que pide selecionar una persona entre una lista de personas"""
    
    PersonaRole = Qt.ItemDataRole.UserRole + 1  # Rol propio para almacenar el objeto persona

    def __init__(self, personas : list[Persona], titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        layout = QVBoxLayout(self)

        self.listaPersonas = QListWidget(self)
        layout.addWidget(self.listaPersonas)

        for persona in personas:
            item = QListWidgetItem(f"{persona.nombre} {persona.apellido}")
            item.setData(self.PersonaRole, QVariant(persona))
            self.listaPersonas.addItem(item)

        self.botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.botones)

        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

    def obtenerPersonaSeleccionada(self) -> Persona:
        itemSeleccionado = self.listaPersonas.currentItem()
        if itemSeleccionado:
            return itemSeleccionado.data(self.PersonaRole)
        else:
            return None
    
class PDFPopupWindow(QDialog):
    """Caja de dialogo que muestra y da las opciones de guardar o imprimir un PDF"""
    
    def __init__(self, rutaPDF, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualizador de PDF")
        self.rutaPDF = rutaPDF
        
        layout = QVBoxLayout()
        self.setLayout(layout)
            
        # No permitir cambiar el tamaño de la ventana popup
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.MSWindowsFixedSizeDialogHint) 
        self.rutaPDF = rutaPDF

        # Crear un QScrollArea para mostrar el contenido del PDF
        scrollArea = QScrollArea()
        layout.addWidget(scrollArea)

        # Crear un QWidget para contener las paginas renderizadas del PDF 
        pdfWidget = QWidget()
        pdfLayout = QVBoxLayout()
        pdfLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pdfWidget.setLayout(pdfLayout)
        scrollArea.setWidget(pdfWidget)

        # Cargar y mostrar el contenido del PDF
        pdfDocumento: fitz.Document = fitz.open(self.rutaPDF)
        for page_num in range(pdfDocumento.page_count):
            page: fitz.Page = pdfDocumento.load_page(page_num)
            pix: fitz.Pixmap = page.get_pixmap()

            # Convertir el pixmap a QImage
            qImage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

            # Crear un QLabel para mostrar la imagen del PDF
            pageLabel = QLabel()
            pageLabel.setPixmap(QPixmap.fromImage(qImage))
            pdfLayout.addWidget(pageLabel)

        # Enable scrolling within the QScrollArea
        scrollArea.setWidgetResizable(True)

        # Create a QHBoxLayout for the buttons
        layoutBotones = QHBoxLayout()

        # Crear un boton para imprimir el PDF
        botonImprimir = QPushButton("Imprimir PDF")
        botonImprimir.clicked.connect(self.impimirPDF)
        layoutBotones.addWidget(botonImprimir)

        # Crear un boton para guardar el PDF
        save_button = QPushButton("Guardar PDF")
        save_button.clicked.connect(self.guardarPDF)
        layoutBotones.addWidget(save_button)

        # Crear un boton para cerrar la ventana
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layoutBotones.addWidget(close_button)

        # Agregar el layout de botones al layout principal
        layout.addLayout(layoutBotones)
        
        # Calcular el tamaño deseado en base al tamaño del contenido
        anchoDeseado = min(layout.sizeHint().width() + 100, self.parentWidget().width() // 2)
        alturaDeseada = min(layout.sizeHint().height() + 200, self.parentWidget().height() // 2)
        self.resize(anchoDeseado, alturaDeseada)

    def impimirPDF(self):
        """Funcion para imprimir el PDF en windows usando win32print"""
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            printer_name = print_dialog.printer().printerName()
            page_range = print_dialog.printer().pageRanges().firstPage(), print_dialog.printer().pageRanges().lastPage()
   
            if printer_name:
                printer_handle = win32print.OpenPrinter(printer_name)
            else:
                printer_handle = win32print.GetDefaultPrinter()

            if page_range:
                start_page, end_page = page_range
                print_range = f'FromPage={start_page} ToPage={end_page}'
            else:
                print_range = ""

            print_parameters = f'"{printer_name}" {print_range}'
            # Print the PDF file
            win32api.ShellExecute(
                0,                  #hwnd
                "printto",          #op
                self.rutaPDF,       #file
                print_parameters,   #params
                None,               #_dir
                0                   #bShow
            )
          
    def guardarPDF(self):
        """Funcion para guardar el pdf"""
        dialogoArchivo = QFileDialog()
        dialogoArchivo.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialogoArchivo.setDefaultSuffix(".pdf")
        rutaArchivo, _ = dialogoArchivo.getSaveFileName(self, "Guardar PDF", "", "Archivos PDF (*.pdf)")
        if rutaArchivo:
            QFile.copy(self.rutaPDF, rutaArchivo)

class EntradaColoresOrganigramaDialog(QDialog):
    """Caja de dialogo que pide los colores editables de una visualización de organigrama GraficoOrganigramaView"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafico: GraficoOrganigramaView = parent.widgetCentral.graficoOrganigrama
        self.setWindowTitle("Cambiar Colores")
        self.setMinimumWidth(150)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.botonColorBordeNodo = QPushButton("Color Borde Nodo")
        self.botonColorBordeNodo.clicked.connect(self.establecerColorBordeNodo)
        layout.addWidget(self.botonColorBordeNodo)
        
        self.botonColorRellenoNodo = QPushButton("Color Relleno Nodo")
        self.botonColorRellenoNodo.clicked.connect(self.establecerColorRellenNodo)
        layout.addWidget(self.botonColorRellenoNodo)
        
        self.botonColorTextoNodo = QPushButton("Color Texto Nodo")
        self.botonColorTextoNodo.clicked.connect(self.establecerColorTextoNodo)
        layout.addWidget(self.botonColorTextoNodo)
        
        self.botonColorLineas = QPushButton("Color Líneas")
        self.botonColorLineas.clicked.connect(self.establecerColorLineas)
        layout.addWidget(self.botonColorLineas)
        
    def establecerColorBordeNodo(self):
        color = QColorDialog.getColor(initial=QColor(self.grafico.colorBordeNodo))
        if color.isValid():
            self.grafico.colorBordeNodo = color.name()
            self.grafico.dibujarArbolOrganigrama()
            
    def establecerColorRellenNodo(self):
        color = QColorDialog.getColor(initial=QColor(self.grafico.colorRellenoNodo))
        if color.isValid():
            self.grafico.colorRellenoNodo = color.name()
            self.grafico.dibujarArbolOrganigrama()
            
    def establecerColorTextoNodo(self):
        color = QColorDialog.getColor(initial=QColor(self.grafico.colorTextoNodo))
        if color.isValid():
            self.grafico.colorTextoNodo = color.name()
            self.grafico.dibujarArbolOrganigrama()
            
    def establecerColorLineas(self):
        color = QColorDialog.getColor(initial=QColor(self.grafico.colorLineas))
        if color.isValid():
            self.grafico.colorLineas = color.name()
            self.grafico.dibujarArbolOrganigrama()
       
class EditorDeOrganigramas(QMainWindow):
    """Clase principal de la Aplicacion""" 
    
    #region RefrescadoDeOrganigrama
    @property
    def archivoEnfocado(self):
        return self._archivoEnfocado

    #Refrescar el archivo enfocado cuando se cambia asignando a el
    @archivoEnfocado.setter
    def archivoEnfocado(self, value : Archivo):
        self._archivoEnfocado = value
        self.refrescarVisualizacionOrganigrama(value)

    def refrescarVisualizacionOrganigrama(self, archivo: Archivo, raiz: NodoArbol = None):
        """
        Funcion que actualiza la visualizacion del archivo en la aplicacion, incluyendo el grafico
        del organigrama, las personas en la barra de herramientas y la fecha de vigente en el estatus.
        Tambien permite visualizar nodo especifico como raiz del organigrama.   
        """
        if self.uiInicializada:
            grafico = self.widgetCentral.graficoOrganigrama
            grafico.archivo = archivo
            # Si especificamos un nodo especifico a visualizar, colocarlo como raiz del grafico
            if raiz is None:
                grafico.raiz = archivo.raiz
            else:
                grafico.raiz = raiz
            # Actualizar elementos de interfaz
            grafico.dibujarArbolOrganigrama()
            grafico.redimensionarGrafico()
            self.actualizarBarraHeramientas()
            self.etiquetaDeEstado.setText(f"Vigente hasta: {archivo.organigrama.fecha.strftime(r'%d/%m/%Y')}")
    #endregion
    
    def __init__(self):
        super().__init__()
        
        self.uiInicializada = False
        """Bandera que asigna cuando se termino de finalizar la interfaz"""
        
        # Cargar archivos 
        self.archivos : dict[str, Archivo] = {}
        """Diccionario de archivos en memoria con codigo de archivo como llave""" 

        self.directorioDeTrabajo = os.getcwd()
        """Directorio donde se ejecuta el programa"""
        
        self.rutaArchivos = os.path.join(self.directorioDeTrabajo, ".Archivos")
        """Ruta donde se guardan archivos internos del programa, incluyendo los archivos de autoguardado/recuperacion"""
        
        self.rutaArchivosRecientes = os.path.join(self.rutaArchivos, "archivos_recientes.dat")
        """Ruta de el archivo que contiene las direcciones de los archivos recientes"""

        self.informador = Informador(self.rutaArchivos)
        """Instancia de clase para generar los informes"""
        
        self.archivoEnfocado = Archivo()
        """Archivo en el que se trabaja actualmente y esta siendo visualizado"""
        
        # Utilizar ruta provisoria para el archivo enfocado
        self.archivoEnfocado.ruta = os.path.join(self.rutaArchivos, "00000.org") 
        self.archivosRecientes = []
        
        # Crear ruta de archivos del programa si no existe
        if not os.path.exists(self.rutaArchivos):
            os.makedirs(self.rutaArchivos)
            # Hacer que el archivo este oculto en windows (en UNIX ya esta oculto con el '.' antes del archivo)
            if platform.system() == "Windows":
                try:
                    import ctypes
                    ATRIBUTO_ARCHIVO_OCULTO = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(self.rutaArchivos, ATRIBUTO_ARCHIVO_OCULTO)
                except Exception as e:
                    print(f"Error ocultando directory: {e}")
        
        # Si no existe la ruta de archivos recientes, crearla como lista vacia
        if not os.path.exists(self.rutaArchivosRecientes):
            self.escribirArchivo(self.rutaArchivosRecientes, self.archivosRecientes)
        else:
            self.archivosRecientes = self.leerArchivo(self.rutaArchivosRecientes)
        
        # Crear un archivo organigrama inicial para el editor
        self.archivoEnfocado = self.crearOrganigrama("Organigrama1", datetime.now())
        self.archivos[self.archivoEnfocado.organigrama.codigo] = self.archivoEnfocado
        
        # Crear widgetCentral
        self.widgetCentral = GraficoOrganigramaWidget(self.archivoEnfocado, self.archivoEnfocado.raiz)
        self.crearElementosDeInterfaz()
        self.uiInicializada = True # Se termino de inicializar la interfaz
    
    def crearElementosDeInterfaz(self):
        """Crear todos los elementos de la interfaz de nuestra aplicacion"""
        self.crearBarraDeHerramientas()                     # Crear barra de herramientas que contiene a las personas
        self.crearBarraDeMenu()                             # Crear barra de menu que contiene a las funciones
        self.crearBarraDeEstado()                           # Crear barra de menu que contiene los organigramas abiertos
        self.setCentralWidget(self.widgetCentral)           # Asignar widget central que contiene visualizacion del organigrama
        
        self.setGeometry(300, 300, 800, 600)                # Asignar el tamaño de la aplicacion
        self.setWindowTitle("Dreamchart")                   # Asignar titulo de la aplicacion
        self.setWindowIcon(QIcon(".\Recursos\Icono.ico"))   # Asignar icono de la aplicacion
     
    def crearBarraDeHerramientas(self):
        """Crear la barra de herramientas que contiene a las personas"""
        # Crear el toolbar
        self.toolbar = QToolBar("Personas", self)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setOrientation(Qt.Orientation.Vertical)

        # Crear un área desplazable para el widget de personas
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setMinimumWidth(200)

        # Crear un widget para contener las personas
        self.personasWidget = QWidget()
        self.personasLayout = QVBoxLayout(self.personasWidget)
        self.personasLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.personasLayout.setSpacing(0)  # Establecer el espaciado entre los botones persona a 0
        self.scrollArea.setWidget(self.personasWidget)
        
        # Añadir una etiqueta para mostrar el título y el recuento de personas
        self.personasEtiqueta = QLabel(f"Personas ({len(self.archivoEnfocado.personasPorCodigo)})")
        self.personasEtiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        font = self.personasEtiqueta.font()
        font.setPointSize(11)
        self.personasEtiqueta.setFont(font)
        self.personasEtiqueta.setContentsMargins(0, 0, 4, 4)
        self.toolbar.addWidget(self.personasEtiqueta)
        
        # Añadir el área de desplazamiento a la barra de herramientas
        self.toolbar.addWidget(self.scrollArea)

        # Añade la barra de herramientas al área derecha de la barra de herramientas
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, self.toolbar)
        
        # Crear el menu contextual para el click derecho a las personas
        self.menuContextual = QMenu(self)

        # Añadir acciones al menú contextual
        eliminarPersona = QAction("Eliminar Persona", self)
        modificarPersona = QAction("Modificar Persona", self)
        asignarPersona = QAction("Asignar Persona a Dependencia", self)

        self.menuContextual.addAction(eliminarPersona)
        self.menuContextual.addAction(modificarPersona)
        self.menuContextual.addAction(asignarPersona)

        # Conectar acciones a sus respectivos slots
        eliminarPersona.triggered.connect(self.contextualEliminarPersona)
        modificarPersona.triggered.connect(self.contextualModificarPersona)
        asignarPersona.triggered.connect(self.contextualAsignarPersona)

        # Añadir un botón para llamar a ingresarPersonas
        ingresarBoton = QAction("＋ Ingresar Persona", self)
        ingresarBoton.triggered.connect(self.menuIngresarPersona)
        self.toolbar.addAction(ingresarBoton)
        
        # Actualizar la barra de herramientas con las personas iniciales
        self.actualizarBarraHeramientas()
        
    def actualizarBarraHeramientas(self):
        """Actualizar la barre de herramientas con las personas que estan en self.archivoEnfocado.personasPorCodigo"""
        # Borrar las personas del layout
        for i in reversed(range(self.personasLayout.count())):
            self.personasLayout.itemAt(i).widget().setParent(None)

        # Agregar las personas al layout como botones individuales
        for persona in self.archivoEnfocado.personasPorCodigo.values():
            button = QPushButton(f"{persona.nombre} {persona.apellido}")
            # Guardar el objeto de persona como propiedad del boton
            button.setProperty("persona", persona)  
            # Conectar el clickeo del boton a clickearPersonaEnLista crearBarraDeHerramientas
            button.clicked.connect(self.clickearPersonaEnLista)
            # Contectar el menu contextual costumizado que creamos
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda event, p=persona: self.mostrarMenuContextual(event, p))
            
            # Cambiar la apariencia del botton usando un stylesheet CSS
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: white;
                    padding: 2px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: lightgray;
                }
                QPushButton:pressed {
                    background-color: silver;
                }
                """
            )    
            button.setFixedWidth(200)
            self.personasLayout.addWidget(button)
       
        # Actualizamos la etiqueta de personas con su cantidad
        self.personasEtiqueta.setText(f"Personas ({len(self.archivoEnfocado.personasPorCodigo)})")

        # Actualizamos la barra de herramientas
        self.toolbar.update()
        
    def clickearPersonaEnLista(self):
        """Esta funcion se llama cuando clickeamos una persona en la lista en la barra de heramientas"""
        # Mostrar detalles de la persona
        
        # Obtenemos el boton que provoco la llamada de esta funcion
        boton = self.sender()
        # Recuperamos el objeto de persona guardado en la propiedad del boton
        persona: Persona = boton.property("persona")
        
        if persona is not None:
            # Mostramos los detalles de la persona en un Messagebox
            mensaje = (
                f"Nombre: {persona.nombre}\n"
                f"Apellido: {persona.apellido}\n"
                f"Documento: {persona.documento}\n"
                f"Teléfono: {persona.telefono}\n"
                f"Dirección: {persona.direccion}\n"
                f"Salario: {persona.salario}\n"
            )
            if self.archivoEnfocado.raiz is not None:
                mensaje +=  f"Dependencia: {self.archivoEnfocado.raiz.buscarNodo(persona.dependencia, NodoArbol.compararCodigo)}\n"
            QMessageBox.information(self, "Detalles de Persona", mensaje)
            
   
    def mostrarMenuContextual(self, event: QPoint, persona: Persona):
        """Funcion para mostrar el menu contextual costumizado al hacer click derecho sobre una persona y permitir realizar funciones"""
        # Guardar la persona seleccionada sobre la cual se abrio el menu contextual
        self.menuContextualPersona = persona

        # Mostrar el menu contextual en la posicion actual del cursor
        self.menuContextual.exec(QCursor.pos())

    def contextualEliminarPersona(self):
        """Eliminar la persona seleccionada en el menu contextual"""
        if self.archivoEnfocado.raiz is not None:
            self.archivoEnfocado.eliminarPersona(self.menuContextualPersona)

        else: #Caso donde se quiere eliminar persona y no existe nodos para recorrer
            self.archivoEnfocado.personasPorCodigo.pop(self.menuContextualPersona.codigo)
        self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def contextualModificarPersona(self):
        """Modificar la persona seleccionada en el menu contextual"""
        self.modificarPersona(self.menuContextualPersona)

    def contextualAsignarPersona(self):
        """Asignar a dependencia la persona seleccionada en el menu contextual"""
        self.asignarPersonaADependencia(self.menuContextualPersona)
            
    def crearBarraDeMenu(self):
        """Crear la barra de menu que contiene a las funciones"""
        menuBar = self.menuBar()

        # Datos del menu
        SEPARADOR_HORIZONTAL = (None, None) # Constante para un separador en el menu dropdown
        menuData = [
            {
                "nombre": "Archivo",
                "acciones": [
                    ("Crear Organigrama", self.menuCrearOrganigrama),
                    SEPARADOR_HORIZONTAL,
                    ("Abrir Recientes", self.menuActualizarArchivosRecientes),
                    ("Abrir Organigrama", self.menuAbrirOrganigrama),
                    SEPARADOR_HORIZONTAL,
                    ("Guardar Organigrama", self.menuGuardarOrganigrama),
                    ("Guardar Organigrama Como", self.menuGuardarOrganigramaComo),
                    SEPARADOR_HORIZONTAL,
                    ("Salir", self.close)
                ]
            },
            {
                "nombre": "Organigrama",
                "acciones": [
                    ("Copiar Organigrama", self.menuCopiarOrganigrama),
                    SEPARADOR_HORIZONTAL,
                    ("Cambiar Nombre de Organigrama", self.menuCambiarNombreOrganigrama),
                    ("Cambiar Fecha de Organigrama", self.menuCambiarFechaOrganigrama),
                    ("Cambiar Colores de Organigrama", self.menuCambiarColoresOrganigrama),
                    SEPARADOR_HORIZONTAL,
                    ("Graficar Organigrama Completo", self.menuGraficarOrganigramaCompleto),
                    ("Graficar Organigrama Por Dependencia", self.menuGraficarOrganigramaPorDependencia),
                ]
            },
            {
                "nombre": "Dependencias",
                "acciones": [
                    ("Crear Dependencia", self.menuCrearDependencia),
                    ("Eliminar Dependencia", self.menuEliminarDependencia),
                    ("Modificar Dependencia", self.menuModificarDependencia),
                    ("Editar Ubicacion Dependencias", self.menuEditarUbicacionDependecias)
                ]
            },
            {
                "nombre": "Personas",
                "acciones": [
                    ("Ingresar Persona", self.menuIngresarPersona),
                    ("Eliminar Persona", self.menuEliminarPersona),
                    ("Modificar Persona", self.menuModificarPersona),
                    ("Asignar Persona a Dependencia", self.menuAsignarPersonaADependencia)
                ]
            },
            {
                "nombre": "Informes",
                "acciones": [
                    ("Personal Por Dependencia", self.menuPersonalPorDependencia),
                    ("Personal por Dependencia Extendido", self.menuPersonalPorDependenciaExtendido),
                    SEPARADOR_HORIZONTAL,
                    ("Salario por Dependencia", self.menuSalarioPorDependencia),
                    ("Salario por Dependencia Extendido", self.menuSalarioPorDependenciaExtendido),
                    SEPARADOR_HORIZONTAL,
                    ("Imprimir Organigrama", self.menuImprimirOrganigrama)
                ]
            },
        ]

        for itemDeMenu in menuData:
            nombreMenu = itemDeMenu["nombre"]
            menu = QMenu(nombreMenu, self)
            menuBar.addMenu(menu)

            for textoDeAccion, funcionDeAccion in itemDeMenu["acciones"]:
                if textoDeAccion is None:
                    menu.addSeparator()
                    continue
                
                # Obtener dinamicamente los archivos recientes y los agregamos al menu
                if textoDeAccion == "Abrir Recientes":
                    submenuNombre = textoDeAccion
                    submenu = QMenu(submenuNombre, self)
                    menu.addMenu(submenu)
                    self.menuActualizarArchivosRecientes(submenu)
                # Si no, agregar normalmente la accion y su funcion al menu
                else:
                    action = QAction(textoDeAccion, self)
                    # Regraficar el organigrama completo cuando realizamos una funcion
                    action.triggered.connect(self.menuGraficarOrganigramaCompleto) 
                    action.triggered.connect(funcionDeAccion)
                    menu.addAction(action)

    def menuActualizarArchivosRecientes(self, submenu: QMenu):
        # Vaciar primero el submenu
        submenu.clear()

        # Obtener los archivos recientes y agregarlos al submenu
        for nombreArchivo in self.archivosRecientes:
            action = QAction(nombreArchivo, self)
            action.triggered.connect(self.abrirArchivoReciente)
            submenu.addAction(action)
                
    def abrirArchivoReciente(self):
        # Obtener texto de la direccion seleccionada
        archivoSeleccionado = self.sender().text()
        # Abrir el archivo que esta en esa direccion
        self.abrirOrganigrama(archivoSeleccionado)
                         
    def crearBarraDeEstado(self):
        """Crear la barra de menu que contiene los organigramas abiertos, su fecha de vigencia y un deslizador de zoom"""
        # Crear un tab bar
        self.tabBarArchivos = QTabBar(self)
        self.tabBarArchivos.setTabsClosable(True)
        self.tabBarArchivos.tabCloseRequested.connect(self.cerrarTabArchivo)
        self.tabBarArchivos.tabBarClicked.connect(self.clickearTabArchivo)
        self.statusBar().addWidget(self.tabBarArchivos)
        # Definir un diccionario para guardar los indices de los tabs con el codigo de archivo como llave
        self.tabIndeces = {}
        # Agregar archivo enfocado a los tabs
        tabIndice = self.tabBarArchivos.addTab(self.archivoEnfocado.organigrama.organizacion)
        self.tabBarArchivos.setCurrentIndex(tabIndice)
        self.tabIndeces[self.archivoEnfocado.organigrama.codigo] = tabIndice
        
        # Agregar etiqueta de estado
        self.etiquetaDeEstado = QLabel(f"Vigente hasta: {self.archivoEnfocado.organigrama.fecha.strftime(r'%d/%m/%Y')}")
        self.statusBar().addWidget(self.etiquetaDeEstado)
        
        # Agregar Deslizador de zoom
        self.zoomWidget = ZoomWidget(vistaDestino=self.widgetCentral.graficoOrganigrama)
        self.statusBar().addPermanentWidget(self.zoomWidget)
        
    def clickearTabArchivo(self, index):
        """Funcion llamada cuando clickeamos un tab de archivo"""
        # Actualizar archivo enfocado cuando cambiamos de tab
        if index != self.tabIndeces[self.archivoEnfocado.organigrama.codigo]:
            codigoArchivoEnTab = [k for k, v in self.tabIndeces.items() if v == index][0]
            self.archivoEnfocado = self.archivos[codigoArchivoEnTab]

    def cerrarTabArchivo(self, index_a_cerrar):
        """Funcion llamada cuando cerramos un tab de archivo"""
        # No cerrar si es el unico archivo abierto
        if len(self.tabIndeces) <= 1:
            mensajeDeError = QMessageBox(parent=self)
            mensajeDeError.setIcon(QMessageBox.Icon.Critical)
            mensajeDeError.setWindowTitle("Error")
            mensajeDeError.setText("No se puede cerrar el unico organigrama abierto!")
            mensajeDeError.exec()
            return

        #Obtener el codigo del archivo a cerrar
        codigoArchivoCerrado = [k for k, v in self.tabIndeces.items() if v == index_a_cerrar][0]
        archivoCerrado = self.archivos[codigoArchivoCerrado]
        # Si el archivo no tiene ruta o tubo cambios mostrar el cuadro de diálogo de confirmación de guardado
        if (archivoCerrado.ruta == "" or archivoCerrado.modificado):
            result = self.mostrarConfirmacionGuardado(archivoCerrado)
            if result == QMessageBox.StandardButton.Save:
                archivoEnfocado = self.archivoEnfocado # Preservar el archivo enfocado anterior
                self.archivoEnfocado = archivoCerrado
                # Si el archivo ya tiene una ruta asociada simplemente guardarlo ahi
                if archivoCerrado.ruta:
                    self.menuGuardarOrganigrama()
                # Si el archivo no tiene una ruta asociada debemos pedir la ruta donde guardar
                else:
                    self.menuGuardarOrganigramaComo()
                self.archivoEnfocado = archivoEnfocado # Reasignar el archivo enfocado preservado
            elif result == QMessageBox.StandardButton.Discard:
                pass  # No importa, descartar archivo y cerrar el tab
            elif result == QMessageBox.StandardButton.Cancel:
                return  # Cancelar, no cerrar el tab
        
        # Eliminar el archivo cerrado
        self.archivos.pop(codigoArchivoCerrado)
        self.tabIndeces.pop(codigoArchivoCerrado)
        
        # Todos los indices a la derecha del tab actual deben ser decrementados por 1
        for k, v in self.tabIndeces.items():
            if v > index_a_cerrar:
                self.tabIndeces[k] = self.tabIndeces[k] - 1
                
        self.tabBarArchivos.removeTab(index_a_cerrar)

        #Actualizar archivo enfocado cuando cambiamos de tab al cerrar un tab
        indiceActual = self.tabBarArchivos.currentIndex()
        codigoArchivoEnTab = [k for k, v in self.tabIndeces.items() if v == indiceActual][0]
        if codigoArchivoEnTab != self.archivoEnfocado.organigrama.codigo:
            self.archivoEnfocado = self.archivos[codigoArchivoEnTab]

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Evento que se llama cuando se usa la rueda del mouse"""
        modifiers = QApplication.keyboardModifiers()
        # Actualizar zoom al hacer ctrl + scrollwheel
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.zoomWidget.updateOnScroll(event)
        # Si no, usar comportamiento normal de scroll
        else:
            super().wheelEvent(event)
   
    def closeEvent(self, event : QCloseEvent):
        """Evento que se llama cuando se cierra la aplicacion, sobreescrita para guardar cambios que no se han guardado"""
        archivosSinGuardar : list[Archivo] = []
        for archivo_code in self.tabIndeces.keys():
            archivo = self.archivos.get(archivo_code)
            # Si el archivo no tiene ruta asociada (nunca fue guardado) o fue modificado sin guardar
            if archivo and (not archivo.ruta or archivo.modificado):
                archivosSinGuardar.append(archivo)

        if archivosSinGuardar:
            for archivo in archivosSinGuardar:
                result = self.mostrarConfirmacionGuardado(archivo)
                if result == QMessageBox.StandardButton.Save:
                    self.archivoEnfocado = archivo
                    # Si el archivo ya tiene una ruta asociada simplemente guardarlo ahi
                    if archivo.ruta:
                        self.menuGuardarOrganigrama()
                    # Si el archivo no tiene una ruta asociada debemos pedir la ruta donde guardar
                    else:
                        self.menuGuardarOrganigramaComo()
                elif result == QMessageBox.StandardButton.Discard:
                    pass  # Descartar cambios
                elif result == QMessageBox.StandardButton.Cancel:
                    event.ignore()  # Cancelar cerrado de aplicacion

            if event.isAccepted():
                event.accept()  # Aceptar cerrado de aplicacion
        else:
            event.accept()  # Aceptar cerrado de aplicacion
 
    def mostrarConfirmacionGuardado(self, archivo):
        """Cuadro de confirmación que pregunta si guardar un archivo, descartar cambios o cancelar la acción"""
        message_box = QMessageBox(parent=self)
        message_box.setWindowTitle("Guardar archivo")
        message_box.setText(f"El archivo '{archivo.organigrama.organizacion}' no está guardado. ¿Desea guardarlo?")

        save_button = message_box.addButton(QMessageBox.StandardButton.Save)
        save_button.setText("Guardar")
        discard_button = message_box.addButton(QMessageBox.StandardButton.Discard)
        discard_button.setText("Descartar")
        cancel_button = message_box.addButton(QMessageBox.StandardButton.Cancel)
        cancel_button.setText("Cancelar")

        message_box.setDefaultButton(QMessageBox.StandardButton.Save)
        return message_box.exec()
      
    def escribirArchivo(self, rutaArchivo, datos) -> None:
        """Escribir los datos de un archivo en la ruta designada con la libreria pickle"""
        with open (rutaArchivo, 'wb') as outf:
            # Serializar los datos con pickle.dumps
            pickled = pickle.dumps(datos, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

    def leerArchivo(self, rutaArchivo):
        """Leer los datos de un archivo en la ruta designada con la libreria pickle"""
        try:
            with open (rutaArchivo, 'rb') as inf:
                if os.path.getsize(rutaArchivo) != 0:
                    # Deserializar los datos con pickle.dumps
                    datos = pickle.load(inf)
            return datos
        except:
            return None

    def crearCodigoOrganigrama(self):
        """Crear el codigo del organigrama"""
        cod = 0
        while str(cod).zfill(5) in self.archivos.keys():
            cod += 1
        return str(cod).zfill(5)
    
    def crearOrganigrama(self, nombre, fecha) -> Archivo:
        """Crea un organigrama con el nombre de organizacion y fecha ingresados"""
        cod = self.crearCodigoOrganigrama()
        nuevo = Archivo()
        nuevo.organigrama.codigo = cod
        nuevo.organigrama.organizacion = nombre
        nuevo.organigrama.fecha = fecha
        self.archivos[cod] = nuevo
        nombreArchivo = f"{nuevo.organigrama.codigo}.org"
        direccion_archivo = os.path.join(self.rutaArchivos, nombreArchivo)
        self.escribirArchivo(direccion_archivo, nuevo)
        return nuevo
    
    def abrirOrganigrama(self, rutaArchivo) -> Archivo:
        """Abrir el organigrama en la ruta ingresada"""        
        # Leer el archivo
        archivo: Archivo = self.leerArchivo(rutaArchivo)
        if archivo is None:
            QMessageBox.critical(self, "Error", "Error al leer el archivo!")
            return
        archivo.ruta = rutaArchivo
        
        # Agregar al los archivos en memoria para poder realizar autoguardado
        self.archivos[archivo.organigrama.codigo] = archivo
        
        # Agregar al tab_bar y seleccionarlo, si el archivo ya estaba abierto seleccionar el tab
        self.archivoEnfocado = archivo
        self.archivoEnfocado.ruta = rutaArchivo

        # Revisar si el tab para el archivo existe, si no crearla
        if archivo.organigrama.codigo in self.tabIndeces.keys():
            indiceTab = self.tabIndeces[archivo.organigrama.codigo]
        else:
            indiceTab = self.tabBarArchivos.addTab(archivo.organigrama.organizacion)
            self.tabIndeces[archivo.organigrama.codigo] = indiceTab
        # Seleccionar el tab del archivo
        self.tabBarArchivos.setCurrentIndex(indiceTab)

        # Si ya existia la ruta en archivos recientes removerla
        if rutaArchivo in self.archivosRecientes:
            self.archivosRecientes.remove(rutaArchivo)
        # Insertar ruta al incio de la lista de archivos recientes
        self.archivosRecientes.insert(0, rutaArchivo)
        
        # Si la cantidad de archivos recientes es mayor a 5, eliminar la direccion mas vieja
        if len(self.archivosRecientes) > 5:
            self.archivosRecientes.pop()
        
        # Guardar la lista de archivos recientes
        self.escribirArchivo(self.rutaArchivosRecientes, self.archivosRecientes)
        
        # Actualizar "Abrir Recientes" en la barra del menu 
        for action in self.menuBar().actions():
            menu: QMenu = action.menu()
            for submenu in menu.actions():
                if submenu.text() == "Abrir Recientes":
                    abrir_recientes_submenu : QMenu = submenu.menu()
                    self.menuActualizarArchivosRecientes(abrir_recientes_submenu)
                    break
            if abrir_recientes_submenu:
                break
            
        # Retornar el archivo leido
        return archivo
    
    def guardarOrganigrama(self, archivo: Archivo):
        """Guarda el archivo del organigrama en su ruta"""
        if not archivo.ruta:
            raise FileNotFoundError(
                f"El archivo del organigrama '{archivo.organigrama.organizacion}' no tiene una ruta asociada.") 
        else:
            archivo.modificado = False # Se guardan los cambios por lo tanto el archivo no estara modificado
            self.escribirArchivo(archivo.ruta, archivo)
        
    def guardarOrganigramaComo(self, archivo: Archivo, rutaDondeGuardar: str):
        """Guarda el archivo del organigrama en la ruta especificada, asignandole esta ruta al objeto archivo"""
        archivo.ruta = rutaDondeGuardar
        self.guardarOrganigrama(archivo)
                
    def copiarOrganigrama(self, archivo: Archivo, organizacion: str, fecha: str):
        """Copia la estructura un orgnaigrama a un nuevo archivo en memoria pero sin copiar las personas"""
        orgCopy : Archivo = copy.deepcopy(archivo)
        orgCopy.organigrama.codigo = self.crearCodigoOrganigrama()
        orgCopy.organigrama.organizacion = organizacion
        orgCopy.organigrama.fecha = fecha
        orgCopy.ruta = ""
        orgCopy.modificado = False
        orgCopy.personasPorCodigo = {}
        orgCopy.raiz.recorrerArbol(NodoArbol.quitarCodigoResponsable)
        self.archivos[orgCopy.organigrama.codigo] = orgCopy
        return orgCopy

    def obtenerTexto(self, title, message, default = None, regex : Tuple[str, str] = None):
        """Obtener texto utilizando una caja de dialogo, cumpliendo con la validacion con el regex pasado"""
        dialog = QInputDialog(self)
        dialog.setLabelText(message)
        dialog.setWindowTitle(title)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setOkButtonText("Aceptar")
        dialog.setCancelButtonText("Cancelar")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        lineEdit: QLineEdit = dialog.findChild(QLineEdit)
        # Si hay un valor predeterminado escribirlo en el campo de texto
        if default:
            lineEdit.setText(default)
        # Si hay una expresion regular utilizarla para validar la entrada de la linea editable
        if regex:
            validator = QRegularExpressionValidator(QRegularExpression(regex[0]), dialog)
            lineEdit.setValidator(validator)
            error_text = f"Valor inválido. {regex[1]}"
            
        # Crear etiqueta de error
        errorLabel = QLabel(dialog)
        errorLabel.setStyleSheet("color: red")
        errorLabel.setText(error_text)
        errorLabel.setVisible(False)

        # Agregar etiqueta de error al layout
        layout: QVBoxLayout = dialog.layout()
        layout.addWidget(errorLabel)
        
        def actualizarErrorLabel():
            if lineEdit.hasAcceptableInput(): 
                errorLabel.setVisible(False) # Cuando la entrada tiene datos aceptables por el validador ocultar el mensaje de error
            else:              
                errorLabel.setVisible(True) # Cuando el validador no permito entrada mostar el mensaje de error  

        # Actualizar la etiqueta de error cuando el validor no permite una entrada o el usuario cambio el texto
        lineEdit.inputRejected.connect(actualizarErrorLabel)
        lineEdit.textChanged.connect(actualizarErrorLabel)

        # Retornar respuesta del dialogo
        if dialog.exec() == QInputDialog.DialogCode.Accepted:
            text = lineEdit.text()
            return text, True
        else:
            return None, False
   
   #region FuncionesDelMenu         
    def menuCrearOrganigrama(self):
        nombre, ok = self.obtenerTexto(
            "Crear Organigrama", 
            "Ingrese el nombre de la organización:", 
            regex=OrganigramaRegex.patrones['organizacion'])
        if ok and nombre:
            dialog = EntradaFechaDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                fecha = dialog.obtenerFecha()
                nuevoArchivo : Archivo = self.crearOrganigrama(nombre, fecha)
                # Enfocar el nuevo archivo
                self.archivoEnfocado = nuevoArchivo     
                # Agregar tab con el nuevo organigrama
                tab_index = self.tabBarArchivos.addTab(nuevoArchivo.organigrama.organizacion)
                self.tabBarArchivos.setCurrentIndex(tab_index)
                self.tabIndeces[nuevoArchivo.organigrama.codigo] = tab_index

    def menuAbrirOrganigrama(self):
        # Dialogo de abrir archivo
        dialogoArchivo = QFileDialog()
        dialogoArchivo.setNameFilter("Archivos de Organigrama (*.org)")
        dialogoArchivo.setDefaultSuffix("org")
        dialogoArchivo.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if dialogoArchivo.exec() == QFileDialog.DialogCode.Accepted:
            archivosSeleccionados = dialogoArchivo.selectedFiles()
            if archivosSeleccionados:
                rutaArchivo = archivosSeleccionados[0]
                # Perform operations with the selected file
                self.abrirOrganigrama(rutaArchivo)
    
    def menuGuardarOrganigrama(self):
        # Si el archivo enfocado ya tiene una ruta de guardado, simplemente guardar
        if self.archivoEnfocado.ruta:
            self.guardarOrganigrama(self.archivoEnfocado)
        # Si no abrir menu de guardar como
        else:
            self.menuGuardarOrganigramaComo()
    
    def menuGuardarOrganigramaComo(self):
        nombrePredeterminado = f"{self.archivoEnfocado.organigrama.organizacion}.org"
        dialogo_archivo = QFileDialog()
        ruta_archivo, _ = dialogo_archivo.getSaveFileName(
            caption="Guardar Organigrama",
            directory=nombrePredeterminado,
            filter="Archivos de Organigrama (*.org)"
        )
        if ruta_archivo:
            self.guardarOrganigramaComo(self.archivoEnfocado, ruta_archivo)

    def menuCopiarOrganigrama(self):
        if self.archivoEnfocado.raiz is not None:
            nombre, ok = self.obtenerTexto(
            "Copiar Organigrama", 
            "Ingrese el nombre de la organización copiada:", 
            regex=OrganigramaRegex.patrones['organizacion'])
        else:
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para copiar. Ingrese una en \"Crear Dependencia\".")
            return
        if ok and nombre:
            dialog = EntradaFechaDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                fecha = dialog.obtenerFecha()
                nuevoArchivo : Archivo = self.copiarOrganigrama(self.archivoEnfocado, nombre, fecha)
                # Enfocar el nuevo archivo
                self.archivoEnfocado = nuevoArchivo 
                # Agregar tab con el nuevo organigrama
                tabIndice = self.tabBarArchivos.addTab(nuevoArchivo.organigrama.organizacion)
                self.tabBarArchivos.setCurrentIndex(tabIndice)
                self.tabIndeces[nuevoArchivo.organigrama.codigo] = tabIndice

    def menuCambiarNombreOrganigrama(self):
        nombreNuevo, ok = self.obtenerTexto(
            "Cambiar Nombre Organigrama", 
            "Ingrese el nuevo nombre para la organización:", 
            regex=OrganigramaRegex.patrones['organizacion'])
        if ok and nombreNuevo:
            self.archivoEnfocado.organigrama.organizacion = nombreNuevo
            # Actualizar nombre de tab
            self.tabBarArchivos.setTabText(self.tabBarArchivos.currentIndex(), nombreNuevo)
    
    def menuCambiarFechaOrganigrama(self):
        dialog = EntradaFechaDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fecha = dialog.obtenerFecha()
            self.archivoEnfocado.organigrama.fecha = fecha
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
    
    def menuCambiarColoresOrganigrama(self):
        if self.archivoEnfocado.raiz is not None:
            dialog = EntradaColoresOrganigramaDialog(self)
            dialog.exec()
        else:
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para cambiar color. Ingrese una en \"Crear Dependencia\".")
            return

    def menuGraficarOrganigramaCompleto(self):
        self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
        
    def menuGraficarOrganigramaPorDependencia(self):
        if self.archivoEnfocado.raiz is not None:
            dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, 
                                                titulo="Dependencia a Graficar:", parent=self)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para graficar. Ingrese una en \"Crear Dependencia\".")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoAGraficar = dialog.nodoSeleccionado()
            self.widgetCentral.graficoOrganigrama.raiz = nodoAGraficar
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado, nodoAGraficar)

    def menuCrearDependencia(self):
        if len(self.archivoEnfocado.codigosDeDependencias) <= 1000:
            nombreDependencia, ok = self.obtenerTexto(
            "Crear Dependencia", 
            f"Ingrese el nombre para la dependencia:", 
            regex=DependenciaRegex.patrones['nombre'])
        else:
            QMessageBox.critical(self, "Error", "Se llego al limite de dependencias! Ya no hay codigos disponibles")
            return
        if ok:
            nodoSeleccionado = None
            if self.archivoEnfocado.raiz is not None:
                dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar la dependencia padre:", parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    nodoSeleccionado = dialog.nodoSeleccionado()
                    # Verificar que no se agreguen mas nodos de lo especificado como maximo
                    if len(nodoSeleccionado.hijos) >= 5:
                        QMessageBox.critical(self, "Error", "La dependencia esta llena! Solo se pueden tener hasta 5 dependencias sucesoras.")
                        return 
            self.archivoEnfocado.crearDependencia(nombreDependencia, nodoSeleccionado)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
        
    def menuEliminarDependencia(self):
        if self.archivoEnfocado.raiz is None:  # Check if there are no options
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para eliminar. Ingrese una en \"Crear Dependencia\".")
            return  # Return without performing any further actions
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar dependencia a eliminar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoSeleccionado = dialog.nodoSeleccionado()
            self.archivoEnfocado.eliminarDependencia(nodoSeleccionado)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def menuModificarDependencia(self):
        if self.archivoEnfocado.raiz is None:  # Verificar si es que no hay opciones
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para modificar. Ingrese una en \"Crear Dependencia\".")
            return  # Retornar sin realizar ninguna accion
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar dependencia a modificar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoSeleccionado = dialog.nodoSeleccionado()
            nombreNuevo, ok = self.obtenerTexto(
            "Modificar Nombre Dependencia", 
            f"Ingrese el nuevo nombre para la dependencia '{nodoSeleccionado.dep.nombre}':", 
            default=f'{nodoSeleccionado.dep.nombre}',
            regex=DependenciaRegex.patrones['nombre'])
            if ok:                  
                nuevoJefeCodigo = None
                #Verificar que existan personas en el organigrama para ser seleccionada como jefe
                if any(self.archivoEnfocado.personasPorCodigo):
                    dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                                    titulo="Ingrese el nuevo jefe para la dependencia:", parent=self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        personaSeleccionada = dialog.obtenerPersonaSeleccionada()
                        nuevoJefeCodigo = personaSeleccionada.codigo
                self.archivoEnfocado.modificarDependencia(nodoSeleccionado.dep.codigo, nombreNuevo, nuevoJefeCodigo)
                self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def menuEditarUbicacionDependecias(self):
        if self.archivoEnfocado.raiz is None:  # Verificar si es que no hay opciones
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama para editar ubicacion. Ingrese una en \"Crear Dependencia\".")
            return  # Retornar sin realizar ninguna accion
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo= "Seleccionar dependencia a mover:", parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoReubicado = dialog.nodoSeleccionado()
            dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, 
                                                 # Excluimos el nodo a mover y sus hijos ya que no tiene sentido logico
                                                 nodosAExcluir=[nodoReubicado],
                                                 titulo="Seleccionar donde ubicar:", 
                                                 parent=self)
            
            if dialog.widgetLista.count() == 0:  # Verificar si es que no hay opciones
                QMessageBox.critical(self, "Error", "Sin opciones disponibles.")
                return  # Retornar sin realizar ninguna accion
            if dialog.exec() == QDialog.DialogCode.Accepted:
                nuevoNodoPadre = dialog.nodoSeleccionado()   
                # Verificar que no se agreguen mas nodos de lo especificado como maximo
                if len(nuevoNodoPadre.hijos) >= 5:
                    QMessageBox.critical(self, "Error", "La dependencia esta llena! Solo se pueden tener hasta 5 dependencias sucesoras.")
                    return 
                if nuevoNodoPadre is not None:
                    self.archivoEnfocado.editarUbicacionDependencia(nodoReubicado, nuevoNodoPadre)
                    self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def menuIngresarPersona(self):
        if len(self.archivoEnfocado.personasPorCodigo.keys()) <= 10000:
            dialog = DatosPersonaDialog(titulo="Crear Persona", parent=self)
        else:
            QMessageBox.critical(self, "Error", "Se llego al limite de personas! Ya no hay codigos disponibles")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            persona = dialog.obtenerPersona()
            self.archivoEnfocado.ingresarPersona(persona)
            self.actualizarBarraHeramientas()

    def menuEliminarPersona(self):

        if any(self.archivoEnfocado.personasPorCodigo): #Verificacion de existencia de personas
                dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                            titulo="Persona a Eliminar:", parent=self)
        else:
            QMessageBox.critical(self, "Error", "No existen personas para eliminar. Ingrese una en \"Ingresar Persona\".")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            personaSeleccionada = dialog.obtenerPersonaSeleccionada()
            if personaSeleccionada is not None:
                if self.archivoEnfocado.raiz is not None:
                    self.archivoEnfocado.eliminarPersona(personaSeleccionada)
                else: #Caso donde se quiere eliminar persona y no hay nodos para recorrer
                    self.archivoEnfocado.personasPorCodigo.pop(personaSeleccionada.codigo)
                self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
                

    def menuModificarPersona(self):
        if any(self.archivoEnfocado.personasPorCodigo):
            dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                    titulo="Persona a Modificar:", parent=self)
        else:
            QMessageBox.critical(self, "Error", "No hay personas para modificar. Ingrese una en \"Ingresar Persona\".")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            personaSeleccionada = dialog.obtenerPersonaSeleccionada()
            self.modificarPersona(personaSeleccionada)
            
    def modificarPersona(self, persona: Persona):
        dialog = DatosPersonaDialog(persona, titulo="Modificar Persona", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            datosPersona = dialog.obtenerPersona()
            self.archivoEnfocado.modificarPersona(persona.codigo, datosPersona)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def menuAsignarPersonaADependencia(self):
        if any(self.archivoEnfocado.personasPorCodigo):
            dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                    titulo="Persona a Asignar:", parent=self)
        else:
            QMessageBox.critical(self, "Error", "No hay personas para asignar. Ingrese una en \"Ingresar Persona\".")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            personaSeleccionada = dialog.obtenerPersonaSeleccionada()
            self.asignarPersonaADependencia(personaSeleccionada)

    def asignarPersonaADependencia(self, persona: Persona):
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo= "Dependencia donde asignar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoSeleccionado = dialog.nodoSeleccionado()
            self.archivoEnfocado.asignarPersonaADependencia(persona.codigo, nodoSeleccionado.dep.codigo)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def pedirNodoParaImprimirInforme(self, funcion):
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccion Dependencia para Informe:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodoSeleccionado = dialog.nodoSeleccionado()
            rutaPDF = funcion(nodoSeleccionado)
            if rutaPDF:
                pdf_popup = PDFPopupWindow(rutaPDF, parent=self)
                pdf_popup.exec()

    def menuPersonalPorDependencia(self):
        if self.archivoEnfocado.raiz is not None:
            funcionInforme = lambda nodo: self.informador.personalPorDependencia(self.archivoEnfocado, nodo.dep)
            self.pedirNodoParaImprimirInforme(funcionInforme)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencia para imprimir. Ingrese una en \"Crear Dependencia\".")

    def menuPersonalPorDependenciaExtendido(self):
        if self.archivoEnfocado.raiz is not None:
            funcionInforme = lambda nodo: self.informador.personalPorDependenciaExtendido(self.archivoEnfocado, nodo)
            self.pedirNodoParaImprimirInforme(funcionInforme)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencia para imprimir. Ingrese una en \"Crear Dependencia\".")

    def menuSalarioPorDependencia(self):
        if self.archivoEnfocado.raiz is not None:
            funcionInforme = lambda nodo: self.informador.salarioPorDependencia(self.archivoEnfocado, nodo.dep)
            self.pedirNodoParaImprimirInforme(funcionInforme)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencia para imprimir salario. Ingrese una en \"Crear Dependencia\".")

    def menuSalarioPorDependenciaExtendido(self):
        if self.archivoEnfocado.raiz is not None:
            funcionInforme = lambda nodo: self.informador.salarioPorDependenciaExtendido(self.archivoEnfocado, nodo)
            self.pedirNodoParaImprimirInforme(funcionInforme)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencia para imprimir salario. Ingrese una en \"Crear Dependencia\".")
    
    def menuImprimirOrganigrama(self):
        if self.archivoEnfocado.raiz is not None:
            ruta = os.path.join(self.rutaArchivos, "Grafico_Organigrama")
            funcionInforme = lambda nodo: self.widgetCentral.graficoOrganigrama.dibujarArbolOrganigramaAPdf(nodo, ruta)
            self.pedirNodoParaImprimirInforme(funcionInforme)
        else:
            QMessageBox.critical(self, "Error", "No hay dependencia para imprimir el organigrama. Ingrese una en \"Crear Dependencia\".")
        
    #endregion       
        
# Ejecucion principal del programa
if __name__ == '__main__':
    aplicacion = QApplication([])
    ventana = EditorDeOrganigramas() # Crear nuestra ventana de aplicacion 
    ventana.showMaximized()
    aplicacion.exec()
