import math
import os
import platform
import copy
import datetime
import pickle
import pickletools

import numpy as np
import graphviz

from functools import partial
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QTimer, QDate, pyqtSignal, QLocale, QRegularExpression
from PyQt6.QtGui import (
    QAction, QMouseEvent, QWheelEvent, QIcon, QFont, QColor, QPen, QPainter, QPixmap, QImage, 
    QRegularExpressionValidator, QValidator, QIntValidator
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QToolBar, QDockWidget, QLineEdit, QPushButton, QTextEdit,
    QSplitter, QWidget, QVBoxLayout, QSizePolicy, QSlider, QSpacerItem, QHBoxLayout, QStackedLayout,
    QFrame, QStyleFactory, QMenu, QMessageBox, QInputDialog, QDateEdit, QCalendarWidget, QDialog,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPixmapItem, QDialogButtonBox,
    QTabBar, QTabWidget, QFileDialog
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *
from Archivo import *
from Informes import *

from typing import Tuple

class OrganizationalChartView(QGraphicsView):
    def __init__(self, root):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.root = root

        self.draw_tree()
        self.center_chart()
        self.prev_size = self.size()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.size() != self.prev_size:
            #print(f"Centrando organigrama")
            self.center_chart()
            self.prev_size = self.size()
        
    def center_chart(self):
        scene_rect = self.scene().itemsBoundingRect()

        # Adjust scene_rect by subtracting the margins
        margin_x = 20
        margin_y = 20
        adjusted_rect = scene_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)

        self.fitInView(adjusted_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    # TODO: static node size with scroll bars being allowed but also the ability to zoom in and out of the widget
    
    # def draw_tree(self):
    #     self.scene().clear()

    #     # Calculate the available space
    #     available_width = self.width()
    #     available_height = self.height()

    #     # Set margins
    #     margin_x = 20
    #     margin_y = 20

    #     # Set initial node width and height
    #     node_width = (available_width - 2 * margin_x) / 5
    #     node_height = (available_height - 2 * margin_y) / 10
    
    #     root_x = margin_x - (node_width / 2)
    #     root_y = margin_y - (node_height / 2)

    #     self.draw_node(self.root, root_x, root_y, node_width, node_height)

    # TODO: opcion para dibujar solo el subarbol de una dependencia/nodo, no el arbol competo
    # TODO: mostrar el nombre del jefe bajo el nombre de la dependencia
    # TODO: hacer que las flechas se comporten 100% como un organigrama
    def draw_tree(self):
        self.scene().clear()

        # Generar el grafo con GraphViz
        dot = graphviz.Digraph(format='svg')
        self.draw_node(dot, self.root)

        dot.graph_attr.update(
            #layout='dot',
            splines='ortho', 
            rankdir='TB')
    
        # Renderizar el grafo como SVG y dibujarlo en la QGraphicsScene del widget
        svg_item = QGraphicsSvgItem()
        svg_renderer = QSvgRenderer(dot.pipe())
        svg_item.setSharedRenderer(svg_renderer)
        self.scene().addItem(svg_item)
        
    def draw_node(self, dot : graphviz.Digraph, node: NodoArbol):
        if node is None:
            return

        # Add the node to the graph
        dot.node(str(id(node)), label=str(node.data), shape="rectangle")

        # Recursively add nodes for each child node
        for child in node.children:
            self.draw_node(dot, child)
            # Add the edge from the parent to the child
            dot.edge(str(id(node)), str(id(child)), arrowhead='none', arrowtail='none', dir='none')
              
class OrganizationalChartWidget(QWidget):
    def __init__(self, root):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.organizational_chart = OrganizationalChartView(root)
        self.layout.addWidget(self.organizational_chart)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.organizational_chart.draw_tree()

class ZoomWidget(QWidget):
    
    
    def __init__(self, target_widget: QGraphicsView, minimum_zoom: int = 10, maximum_zoom: int = 400, parent=None):
        super().__init__(parent)
        self.target_widget = target_widget
        self.minimum_zoom = minimum_zoom
        self.maximum_zoom = maximum_zoom
        self.setup_ui()

    def setup_ui(self):
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(self.minimum_zoom)
        self.zoom_slider.setMaximum(self.maximum_zoom)
        self.middle_zoom = (self.minimum_zoom + self.maximum_zoom) / 2
        self.zoom_slider.setSliderPosition(int(self.middle_zoom))
        self.zoom_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.zoom_slider.setTickInterval(1)

        self.zoom_slider.setSingleStep(1)
        self.zoom_slider.setPageStep(1)
        self.zoom_slider.setMaximumWidth(200)  # Adjust the maximum width here
        self.zoom_slider.setFixedHeight(20) # Makes the slider the same height as the buttons

        self.zoom_slider.valueChanged.connect(self.update_zoom)

        self.zoom_percentage = QLabel("100%")
        self.zoom_percentage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_percentage.setStyleSheet("color: dimgrey; padding-bottom: 3.5px;")
        self.zoom_percentage.setFixedWidth(30)  # Set a fixed width for the label that considers the max width of 100%
             
        container_widget = QWidget()

        layout = QHBoxLayout(container_widget)
        layout.setContentsMargins(0, 0, 10, 0)  # Set right margin
        layout.setSpacing(0)  # Set spacing between items
        layout.addStretch(1)  # Add stretch to align items to the right

        
        # TODO: Try QToolButton with autorepeat to simplify timer logic? (not worth maybe since this works already..)
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: center; /* Center-align the text */
                padding-bottom: 3.5px; /* Adjust the padding to vertically center the text */
                color: dimgrey;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 40);
            }
        """

        minus_button = QPushButton("－")
        minus_button.setFixedSize(20, 20)
        minus_button.setStyleSheet(button_style)
        minus_button.pressed.connect(partial(self.start_zoom_timer, -10))
        minus_button.released.connect(self.stop_zoom_timer)
        minus_button.clicked.connect(partial(self.increment_zoom, -10))

        plus_button = QPushButton("＋")
        plus_button.setFixedSize(20, 20)
        plus_button.setStyleSheet(button_style)
        plus_button.pressed.connect(partial(self.start_zoom_timer, 10))
        plus_button.released.connect(self.stop_zoom_timer)
        plus_button.clicked.connect(partial(self.increment_zoom, 10))

        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(False)
        self.zoom_timer.timeout.connect(self.handle_zoom_timer)

        layout.addWidget(minus_button)
        layout.addWidget(self.zoom_slider, 1)
        layout.addWidget(plus_button)
        layout.addWidget(self.zoom_percentage)
        
        self.setLayout(layout)
                      
    # Middle line of the slider widget to indicate the 100% mark
    def paintEvent(self, event):
        super().paintEvent(event)  # Call the base class paintEvent first
        painter = QPainter(self)    
        pen = QPen(QColor(215, 215, 215))
        pen.setWidth(2) # Draw a line with width of 2 pixels
        painter.setPen(pen)
        
        slider_rect_center = self.zoom_slider.geometry().center()
        painter.drawLine(slider_rect_center.x(), slider_rect_center.y() - 7, 
                         slider_rect_center.x(), slider_rect_center.y() + 7)
        
        # Keep zoom when resizing
        #if self.target_widget.size() != self.target_widget.prev_size:
        #    self.update_zoom(self.zoom_slider.value())
        #    self.target_widget.prev_size = self.target_widget.size()
        
    def start_zoom_timer(self, step):
        if not self.zoom_timer.isActive():
            self.zoom_timer_step = step
            self.zoom_timer_interval = 300  # Adjust the initial interval here
            self.zoom_timer.setInterval(self.zoom_timer_interval)
            self.zoom_timer.start()

    def stop_zoom_timer(self):
        if self.zoom_timer.isActive():
            self.zoom_timer.stop()

    def handle_zoom_timer(self):
        if self.zoom_timer.interval() == 300:  # First invocation
            self.zoom_timer_interval = 100  # Adjust the new interval here
        self.increment_zoom(self.zoom_timer_step)

    def increment_zoom(self, step=None):
        # Cuando estamos manteniendo apretado el boton usar el timer
        if step is None:
            step = self.zoom_timer_step
            
        current_value = self.zoom_slider.value()
        
        # # TODO: Fix rounding of step by linearly mapping step on both sides of the middle_zoom value
        # print(self.minimum_zoom, self.maximum_zoom, self.middle_zoom, step, current_value)

        # Map the step with the different linear scales
        #print(current_value)
        if current_value == self.middle_zoom:
            if step < 0:
                normalizer = (self.middle_zoom - self.minimum_zoom) / (100 - self.minimum_zoom)
            else:
                normalizer = (self.maximum_zoom - self.middle_zoom) / (self.maximum_zoom - 100)
        elif current_value < self.middle_zoom:
            normalizer = (self.middle_zoom - self.minimum_zoom) / (100 - self.minimum_zoom)
        else:
            normalizer = (self.maximum_zoom - self.middle_zoom) / (self.maximum_zoom - 100) 
        
        step = step * normalizer
        step = round(step)
        #print(f"Mapped step: {mapped_step}")
                
        # TODO: volver a hacer que funcione el redondeo?
        #Redondear el valor incrementado/decrementado al valor mas cercano divisible por el step
        # if current_value % step == 0:
        #    print(f"{current_value} is an even 10% step")
        #    new_value = current_value + step
        # else:
        #    new_value = math.ceil(current_value / step) * step
        #    print(f"{current_value} got rounded to {new_value} with step {step}")
        
        new_value = current_value + step
        new_value = max(self.minimum_zoom, min(self.maximum_zoom, new_value))
        self.zoom_slider.setValue(new_value)

        # Adjust the timer interval based on the duration the button is held down
        self.zoom_timer_interval -= 10
        self.zoom_timer_interval = max(30, self.zoom_timer_interval)
        self.zoom_timer.setInterval(self.zoom_timer_interval)
        
    def update_zoom(self, value):                
        if value <= self.middle_zoom:
            zoom_factor = 1.0 - (1.0 - (value - self.minimum_zoom) / (self.middle_zoom - self.minimum_zoom)) * (1.0 - self.minimum_zoom / 100)
        else:
            zoom_factor = 1.0 + (value - self.middle_zoom) / (self.maximum_zoom - self.middle_zoom) * (self.maximum_zoom / 100 - 1.0)

        # Snap when the value is close to 100% zoom (middle of slider)
        if 0.9 < zoom_factor < 1.09:    
            value = self.middle_zoom
            self.zoom_slider.setSliderPosition(int(self.middle_zoom))
            zoom_factor = 1.0
            
        #zoom_percentage = f"{round(zoom_factor * 100)}% factor: {zoom_factor:.4}"
        zoom_percentage = f"{round(zoom_factor * 100)}%"
        self.zoom_percentage.setText(zoom_percentage)

        self.target_widget.resetTransform()
        self.target_widget.scale(zoom_factor, zoom_factor)  
             
    def updateOnScroll(self, event: QWheelEvent):
        delta = event.angleDelta().y() / 120  # Get scroll wheel delta
        step = 10  # Set the zoom step
        zoom_value = self.zoom_slider.value()
        new_zoom_value = max(self.minimum_zoom, min(self.maximum_zoom , zoom_value + (delta * step)))
        self.zoom_slider.setValue(new_zoom_value)

class DateInputDialog(QDialog):
    accepted = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar fecha")
        
        calendar_widget = QCalendarWidget()
        calendar_widget.setGridVisible(True)
        calendar_widget.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar_widget.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        calendar_widget.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        calendar_widget.setLocale(QLocale())
        calendar_widget.setMinimumDate(QDate(1900, 1, 1))
        calendar_widget.setMaximumDate(QDate(2100, 12, 31))
        calendar_widget.setSelectedDate(QDate.currentDate())
        layout = QVBoxLayout()
        layout.addWidget(calendar_widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        self.calendar_widget = calendar_widget
    
    def getDate(self):
        return self.calendar_widget.selectedDate().toPyDate()
    
class EditorDeOrganigramas(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        # Cargar archivos 
        self.archivos : dict[str, Archivo] = {}
        """Diccionario de archivos en memoria con codigo de archivo como llave""" 

        self.directorio_de_trabajo = os.getcwd()
        self.ruta_archivos = os.path.join(self.directorio_de_trabajo, ".Archivos")
        """Ruta donde se guardan archivos internos del programa, incluyendo los archivos de autoguardado/recuperacion"""
        self.ruta_archivos_recientes = os.path.join(self.ruta_archivos, "archivos_recientes.dat")
        
        self.archivoEnfocado = Archivo()
        self.archivoEnfocado.ruta = os.path.join(self.ruta_archivos, "00000.org")
        self.archivosRecientes = []
        
        # Crear ruta de archivos del programa si no existe
        if not os.path.exists(self.ruta_archivos):
            os.makedirs(self.ruta_archivos)
            # Hacer que el archivo este oculto en windows (en UNIX ya esta oculto con el '.' antes del archivo)
            if platform.system() == "Windows":
                try:
                    import ctypes
                    ATRIBUTO_ARCHIVO_OCULTO = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(self.ruta_archivos, ATRIBUTO_ARCHIVO_OCULTO)
                except Exception as e:
                    print(f"Error ocultando directory: {e}")
        
        if not os.path.exists(self.ruta_archivos_recientes):
            self.escribir_archivo(self.ruta_archivos_recientes, self.archivosRecientes)
        else:
            self.archivosRecientes = self.leer_archivo(self.ruta_archivos_recientes)
            
        if not os.path.exists(self.archivoEnfocado.ruta):
            self.archivoEnfocado = self.crearOrganigrama("Organigrama1", datetime.now())
        else:
            self.archivoEnfocado = self.leer_archivo(self.archivoEnfocado.ruta)
        
        self.archivos[self.archivoEnfocado.organigrama.codigo] = self.archivoEnfocado
            
        # for file in os.listdir(self.ruta_archivos):
        #     dir = self.ruta_archivos + '\\' + file
        #     temp : Archivo = self.leer_archivo(dir)
        #     if temp != None:
        #         self.archivos[temp.organigrama.codigo] = temp
                
        # print(self.archivos)
        # print(type(self.archivos))

        persona = Persona(codigo="1011", dependencia="202", nombre="Juan", apellido = "Perez")
        print(persona)
        print(persona.__repr__())
        persona.salario = 100000000
        persona.codigo = "1233"  


        fecha = datetime.now()
        #self.crearOrganigrama('Cesars', fecha)
        #print(self.archivos)
        #self.crearOrganigrama('Chau', fecha)
        #print(self.archivos)
        temp =  self.archivoEnfocado
        temp.crearDependencia("Gotocesars", temp.raiz)
        dep = temp.raiz.buscar_nodo("000", NodoArbol.compararCodigo)
        print(dep)
        temp.ingresarPersona("Fabri", "Kawabata", "5406655", "0972399578", "Angel Torres", 1234)
        temp.ingresarPersona("Hiroto", "Yamashita", "2348932", "2384123", "Mcal. Estigarribia", 2345)
        temp.asignarPersonaADependencia("0000", "000", True)
        individuo = temp.personasPorCodigo["0000"]
        print(individuo)
        print(temp.raiz.data)
        temp.raiz.recorrerOrganigrama("0000", NodoArbol.quitarJefe)
        print(temp.raiz.data)
        temp.asignarPersonaADependencia("0001", "000", True)
        print(temp.raiz.data)

    
        # Crear el árbol
        raiz = NodoArbol(Dependencia(codigo='001', codigoResponsable='1234', nombre='Dependencia A'))
        
        hijo_1 = NodoArbol(Dependencia(codigo='002', codigoResponsable='5678', nombre='Dependencia B'))
        hijo_2 = NodoArbol(Dependencia(codigo='003', codigoResponsable='9012', nombre='Dependencia C'))
        hijo_3 = NodoArbol(Dependencia(codigo='006', codigoResponsable='9013', nombre='Dependencia F'))

        nieto_1 = NodoArbol(Dependencia(codigo='004', codigoResponsable='3456', nombre='Dependencia D'))
        nieto_2 = NodoArbol(Dependencia(codigo='005', codigoResponsable='7890', nombre='Dependencia E'))
        nieto_3 = NodoArbol(Dependencia(codigo='007', codigoResponsable='9014', nombre='Dependencia G'))
        nieto_4 = NodoArbol(Dependencia(codigo='008', codigoResponsable='9015', nombre='Dependencia H'))
        nieto_5 = NodoArbol(Dependencia(codigo='009', codigoResponsable='9016', nombre='Dependencia I'))
        nieto_6 = NodoArbol(Dependencia(codigo='010', codigoResponsable='9017', nombre='Dependencia J'))


        raiz.agregar_hijo(hijo_1)
        raiz.agregar_hijo(hijo_2)
        raiz.agregar_hijo(hijo_3)

        hijo_1.agregar_hijo(nieto_1)
        hijo_1.agregar_hijo(nieto_2)
        hijo_2.agregar_hijo(nieto_3)
        hijo_2.agregar_hijo(nieto_4)
        hijo_3.agregar_hijo(nieto_5)
        hijo_3.agregar_hijo(nieto_6)

        # Imprimir la estructura del árbol
        def imprimir_arbol(nodo, nivel=0):
            print('  ' * nivel + '- ' + str(nodo))
            for hijo in nodo.children:  
                imprimir_arbol(hijo, nivel + 1)

       
        imprimir_arbol(raiz)

        #TODO: segmentar guardado de archivos
        archivo : Archivo = Archivo()
        archivo.raiz = raiz
        
        print("Archivo guardado:\n")
        with open('archivo.dat', 'wb') as outf:
            pickled = pickle.dumps(archivo, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

        with open('archivo.dat', 'rb') as inf:
            archivo = pickle.load(inf)
            imprimir_arbol(archivo.raiz)
        
        def compararCodigo(nodo : NodoArbol, codigo):
            return nodo.data.codigo == codigo
        
        print("Nodo encontrado:")
        encontrado = raiz.buscar_nodo('005', compararCodigo)
        print(encontrado)
        print("Padre de encontrado:")
        print(encontrado.padre(raiz))


        persona1 = Persona(codigo="1011", dependencia="002", nombre="Juan", apellido = "Perez", salario=50000)
        persona2 = Persona(codigo="1012", dependencia="002", nombre="Pedro", apellido = "Pascal", salario=565656)
        persona3 = Persona(codigo="1013", dependencia="002", nombre="Poroto", apellido = "Manteca", salario=636363)
        persona4 = Persona(codigo="1014", dependencia="002", nombre="El", apellido = "Ivan", salario=5959595)
        persona5 = Persona(codigo="1015", dependencia="002", nombre="Fabrizio", apellido = "K", salario=200000)
        persona6 = Persona(codigo="1016", dependencia="004", nombre="Martin", apellido = "F", salario=19191919)
        persona7 = Persona(codigo="1017", dependencia="004", nombre="Javier", apellido = "G", salario=666666)
        persona8 = Persona(codigo="1018", dependencia="008", nombre="Filippi", apellido = "Profe", salario=100000)
        persona9 = Persona(codigo="1019", dependencia="005", nombre="Ivan", apellido = "Aux", salario=10000)
        persona10 = Persona(codigo="1020", dependencia="010", nombre="Jhonny", apellido = "Test", salario=10000)
        archivo.personasPorCodigo[persona1.codigo] = persona1
        archivo.personasPorCodigo[persona2.codigo] = persona2
        archivo.personasPorCodigo[persona3.codigo] = persona3
        archivo.personasPorCodigo[persona4.codigo] = persona4
        archivo.personasPorCodigo[persona5.codigo] = persona5
        archivo.personasPorCodigo[persona6.codigo] = persona6
        archivo.personasPorCodigo[persona7.codigo] = persona7
        archivo.personasPorCodigo[persona8.codigo] = persona8
        archivo.personasPorCodigo[persona9.codigo] = persona9
        archivo.personasPorCodigo[persona10.codigo] = persona10

        hijo_1.data.codigoResponsable = persona5.codigo
        
        # Informes
        Informes.personalPorDependencia(archivo, hijo_1.data)
        Informes.salarioPorDependencia(archivo, hijo_1.data)
        Informes.salarioPorDependenciaExtendido(archivo, raiz)
        Informes.personalPorDependenciaExtendido(archivo, hijo_1)

        # Application setup
        # Set the window title and size
        self.setWindowTitle("Editor De Organigramas")
        self.setGeometry(100, 100, 400, 200)
        
        self.central_widget = OrganizationalChartWidget(raiz)
        self.init_ui()
        
        # Agregar tab inicial TODO: mover a posicion adecuada en init_ui
        tab_index = self.tab_bar_archivos.addTab(self.archivoEnfocado.organigrama.organizacion)
        self.tab_bar_archivos.setCurrentIndex(tab_index)
        self.tab_indexes[self.archivoEnfocado.organigrama.codigo] = tab_index
        
        QTimer.singleShot(1000, self.saveScreenshot)
        QTimer.singleShot(1000, self.save_chart_as_png)
    
    def save_chart_as_png(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.central_widget.organizational_chart.winId() )
        screenshot.save('chart.png', 'png')

    def saveScreenshot(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.winId() )
        screenshot.save('screenshot.png', 'png')
    
    def init_ui(self):
        self.create_toolbar()
        self.create_menu_bar()
        self.create_status_bar()
        self.set_central_widget()
    
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Dreamchart")
        self.setWindowIcon(QIcon("E:\Cursos\Facultad\Semestres\2ndoSemestre\MateriasFPUNA\AlgoritmosYEstructuraDeDatos2\EditorDeOrganigramas\EditorDeOrganigramas\Interfaz\Icono.ico"))
        self.show()
     
    def create_toolbar(self):
        self.toolbar = QToolBar("Properties", self)

        label1 = QLabel("Property 1:")
        label2 = QLabel("Property 2:")
        text_field1 = QLineEdit()
        text_field2 = QLineEdit()

        self.toolbar.addWidget(label1)
        self.toolbar.addWidget(text_field1)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(label2)
        self.toolbar.addWidget(text_field2)

        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, self.toolbar)

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # Datos del menu
        SEPARADOR_HORIZONTAL = (None, None) # Constante para un separador en el menu dropdown
        menu_data = [
            {
                "label": "Archivo",
                "actions": [
                    ("Abrir Recientes", self.actualizar_archivos_recientes),
                    ("Guardar Organigrama", self.guardar_organigrama),
                    ("Guardar Organigrama Como", self.guardar_organigrama_como),
                    SEPARADOR_HORIZONTAL,
                    ("Exit", self.close)
                ]
            },
            {
                "label": "Organigrama",
                "actions": [
                    ("Crear Organigrama", self.crear_organigrama),
                    ("Abrir Organigrama", self.abrir_organigrama),
                    ("Crear Dependencia", self.crear_dependencia),
                    ("Eliminar Dependencia", self.eliminar_dependencia),
                    ("Modificar Dependencia", self.modificar_dependencia),
                    ("Editar Ubicacion Dependencias", self.editar_ubicacion_dependencias),
                    ("Copiar Organigrama", self.copiar_organigrama),
                    ("Graficar Organigrama", self.graficar_organigrama)
                ]
            },
            {
                "label": "Personas",
                "actions": [
                    ("Ingresar Personas", self.ingresar_personas),
                    ("Eliminar Personas", self.eliminar_personas),
                    ("Modificar Personas", self.modificar_personas),
                    ("Asignar Personas a Dependencias", self.asignar_personas_dependencias)
                ]
            },
            {
                "label": "Informes",
                "actions": [
                    ("Personal Por Dependencia", self.personal_por_dependencia),
                    ("Personal por Dependencia Extendido", self.personal_por_dependencia_extendido),
                    ("Salario por Dependencia", self.salario_por_dependencia),
                    ("Salario por Dependencia Extendido", self.salario_por_dependencia_extendido),
                    ("Imprimir Organigrama", self.imprimir_organigrama)
                ]
            },
            {
                "label": "Ayuda",
                "actions": [
                ]
            },
        ]

        for menu_item in menu_data:
            menu_label = menu_item["label"]
            menu = QMenu(menu_label, self)
            menu_bar.addMenu(menu)

            for action_text, action_data in menu_item["actions"]:
                if action_text is None:
                    menu.addSeparator()
                    continue
                
                # Obtener dinamicamente los archivos recientes y los agregamos al menu
                if action_text == "Abrir Recientes":
                    submenu_label = action_text
                    submenu = QMenu(submenu_label, self)
                    menu.addMenu(submenu)
                    self.actualizar_archivos_recientes(submenu)
                else:
                    action = QAction(action_text, self)
                    action.triggered.connect(action_data)
                    menu.addAction(action)

    def actualizar_archivos_recientes(self, submenu: QMenu):
        # Clear the submenu first
        submenu.clear()

        # Obtain the recent files and add them to the submenu
        for file_name in self.archivosRecientes:
            action = QAction(file_name, self)
            action.triggered.connect(self.open_recent_file)
            submenu.addAction(action)
                
    def open_recent_file(self):
        # Handle the action for opening a recent file
        # Retrieve the selected file and open it
        selected_file = self.sender().text()
        # Add your code to open the file
        self.abrirOrganigrama(selected_file)
                         
    def create_status_bar(self):
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        
        # Create a tab bar
        self.tab_bar_archivos = QTabBar(self)
        self.tab_bar_archivos.setTabsClosable(True)
        self.tab_bar_archivos.tabCloseRequested.connect(self.cerrarTabArchivo)
        self.tab_bar_archivos.tabBarClicked.connect(self.clickearTabArchivo)
        self.statusBar().addWidget(self.tab_bar_archivos)
        # Define a dictionary to store tab indexes
        self.tab_indexes = {}
        
        self.zoom_widget = ZoomWidget(target_widget=self.central_widget.organizational_chart)
        self.statusBar().addPermanentWidget(self.zoom_widget)
        
    def clickearTabArchivo(self, index):
        # Actualizar archivo enfocado cuando cambiamos de tab
        if index != self.tab_indexes[self.archivoEnfocado.organigrama.codigo]:
            codigo_archivo_en_tab = [k for k, v in self.tab_indexes.items() if v == index][0]
            self.archivoEnfocado = self.archivos[codigo_archivo_en_tab]
            # TODO: Remover print
            print(f"Enfoco archivo {self.archivos[codigo_archivo_en_tab].organigrama.organizacion} tab {index}")

    def cerrarTabArchivo(self, index_a_cerrar):
            # No cerrar si es el unico archivo abierto
            if len(self.tab_indexes) <= 1:
                error_message = QMessageBox()
                error_message.setIcon(QMessageBox.Icon.Critical)
                error_message.setWindowTitle("Error")
                error_message.setText("No se puede cerrar el unico organigrama abierto!")
                error_message.exec()
                return

            # Eliminar el archivo cerrado
            codigo_archivo_cerrado = [k for k, v in self.tab_indexes.items() if v == index_a_cerrar][0]
            self.archivos.pop(codigo_archivo_cerrado)
            self.tab_indexes.pop(codigo_archivo_cerrado)
            
            # Todos los indices a la derecha del tab actual deben ser decrementados por 1
            for k, v in self.tab_indexes.items():
                if v > index_a_cerrar:
                    self.tab_indexes[k] = self.tab_indexes[k] - 1
                    
            self.tab_bar_archivos.removeTab(index_a_cerrar)

            #Actualizar archivo enfocado cuando cambiamos de tab al cerrar un tab
            current_index = self.tab_bar_archivos.currentIndex()
            codigo_archivo_en_tab = [k for k, v in self.tab_indexes.items() if v == current_index][0]
            if codigo_archivo_en_tab != self.archivoEnfocado.organigrama.codigo:
                self.archivoEnfocado = self.archivos[codigo_archivo_en_tab]
                # TODO: Remover print
                print(f"Enfoco archivo {self.archivos[codigo_archivo_en_tab].organigrama.organizacion} tab {index_a_cerrar}")

    def set_central_widget(self):
        self.setCentralWidget(self.central_widget)

        self.central_widget.setMouseTracking(True)  # Enable mouse tracking for central widget
        self.central_widget.mouseMoveEvent = self.mouse_move_event
        self.central_widget.mousePressEvent = self.mouse_press_event
        self.central_widget.mouseReleaseEvent = self.mouse_release_event

    def wheelEvent(self, event: QWheelEvent) -> None:
        modifiers = QApplication.keyboardModifiers()
        # Actualizar zoom al hacer ctrl + scrollwheel
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.zoom_widget.updateOnScroll(event)
        # Si no, usar comportamiento normal de scroll
        else:
            super().wheelEvent(event)
                              
    def mouse_move_event(self, event):
        # Handle mouse move event
        pos = event.pos()
        self.status_label.setText(f"Mouse position: ({pos.x()}, {pos.y()})")

    def mouse_press_event(self, event):
        # Handle mouse press event
        pos = event.pos()
        self.status_label.setText(f"Mouse clicked at: ({pos.x()}, {pos.y()})")

    def mouse_release_event(self, event):
        # Handle mouse release event
        pos = event.pos()
        self.status_label.setText(f"Mouse released at: ({pos.x()}, {pos.y()})")
        #self.status_label.clear()
        
    def escribir_archivo (self, nombre_archivo, datos) -> None:
        with open (nombre_archivo, 'wb') as outf:
            pickled = pickle.dumps(datos, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

    def leer_archivo (self, nombre_archivo):
        with open (nombre_archivo, 'rb') as inf:
            if os.path.getsize(nombre_archivo) != 0:
                datos = pickle.load(inf)
        return datos

    # TODO: Arreglar
    def crearCodigoOrganigrama(self):
        cod = 0
        while str(cod).zfill(5) in self.archivos.keys():
            cod += 1
        return str(cod).zfill(5)
    
    def crearOrganigrama(self, nombre, fecha) -> Archivo:
        cod = self.crearCodigoOrganigrama()
        nuevo = Archivo()
        nuevo.organigrama.codigo = cod
        nuevo.organigrama.organizacion = nombre
        nuevo.organigrama.fecha = fecha
        self.archivos[cod] = nuevo
        nombre_archivo = f"{nuevo.organigrama.codigo}.org"
        direccion_archivo = os.path.join(self.ruta_archivos, nombre_archivo)
        print(direccion_archivo)
        self.escribir_archivo(direccion_archivo, nuevo)
        return nuevo
    
    def abrirOrganigrama(self, rutaArchivo) -> Archivo:        
        # Leer el archivo
        archivo : Archivo = self.leer_archivo(rutaArchivo)
        archivo.ruta = rutaArchivo
        
        # Agregar al los archivos en memoria para poder realizar autoguardado
        # TODO: que pasa si el codigo ya existe? reasignar un nuevo codigo?
        self.archivos[archivo.organigrama.codigo] = archivo
        
        # Agregar al tab_bar y seleccionarlo, si el archivo ya estaba abierto seleccionar el tab
        self.archivoEnfocado = archivo
        self.archivoEnfocado.ruta = rutaArchivo

        # Revisar si el tab para el archivo existe, si no crearla
        if archivo.organigrama.codigo in self.tab_indexes.keys():
            tab_index = self.tab_indexes[archivo.organigrama.codigo]
        else:
            tab_index = self.tab_bar_archivos.addTab(archivo.organigrama.organizacion)
            self.tab_indexes[archivo.organigrama.codigo] = tab_index
        # Seleccionar el tab del archivo
        self.tab_bar_archivos.setCurrentIndex(tab_index)

        # Si ya existia la ruta en archivos recientes removerla
        if rutaArchivo in self.archivosRecientes:
            self.archivosRecientes.remove(rutaArchivo)
        # Insertar ruta al incio de la lista de archivos recientes
        self.archivosRecientes.insert(0, rutaArchivo)
        
        # Si la cantidad de archivos recientes es mayor a 5, eliminar la direccion mas vieja
        if len(self.archivosRecientes) > 5:
            self.archivosRecientes.pop()
        
        # Guardar la lista de archivos recientes
        self.escribir_archivo(self.ruta_archivos_recientes, self.archivosRecientes)
        
        # Actualizar "Abrir Recientes" en la barra del menu 
        for action in self.menuBar().actions():
            menu: QMenu = action.menu()
            for submenu in menu.actions():
                if submenu.text() == "Abrir Recientes":
                    abrir_recientes_submenu : QMenu = submenu.menu()
                    self.actualizar_archivos_recientes(abrir_recientes_submenu)
                    break
            if abrir_recientes_submenu:
                break
            
        # Retornar el archivo leido
        return archivo
    
    def autoGuardadoDeOrganigramas(self):
        pass
    
    def guardarOrganigrama(self, archivo: Archivo):
        # Si el archivo no tiene ruta tirar error
        if not archivo.ruta:
            raise FileNotFoundError() # TODO: mensaje de error
        else:
            self.escribir_archivo(archivo.ruta, archivo)
        
    def guardarOrganigramaComo(self, archivo: Archivo, rutaDondeGuardar: str):
        archivo.ruta = rutaDondeGuardar
        self.guardarOrganigrama(archivo)
                
    def copiarOrganigrama(self, codigoOrg, organizacion, fecha):
        orgCopy : Archivo = copy.deepcopy(self.archivos[codigoOrg])
        orgCopy.organigrama.codigo = self.crearCodigoOrganigrama()
        orgCopy.organigrama.organizacion = organizacion
        orgCopy.organigrama.fecha = fecha
        orgCopy.personasPorCodigo = {}
        orgCopy.quitarCodres(orgCopy.raiz)

    def getText(self, title, message, regex : Tuple[str, str] = None, bounds = None):
        dialog = QInputDialog(self)
        dialog.setLabelText(message)
        dialog.setWindowTitle(title)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setOkButtonText("Aceptar")
        dialog.setCancelButtonText("Cancelar")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        line_edit: QLineEdit = dialog.findChild(QLineEdit)

        if regex:
            validator = QRegularExpressionValidator(QRegularExpression(regex[0]), dialog)
            line_edit.setValidator(validator)
            error_text = f"Valor inválido. {regex[1]}"
        elif bounds:
            min_val, max_val = bounds
            validator = QIntValidator(min_val, max_val, dialog)
            line_edit.setValidator(validator)
            error_text = f"El valor debe estar entre {min_val} y {max_val}"

        # Create error label
        error_label = QLabel(dialog)
        error_label.setStyleSheet("color: red")
        error_label.setText(error_text)
        error_label.setVisible(False)

        # Add error label to dialog layout
        layout: QVBoxLayout = dialog.layout()
        layout.addWidget(error_label)
        
        def update_error_label():
            if line_edit.hasAcceptableInput():
                error_label.setVisible(False)
            else:
                error_label.setVisible(True)

        # Connect signal to update error label visibility and text
        line_edit.inputRejected.connect(update_error_label)
        line_edit.textChanged.connect(update_error_label)

        if dialog.exec() == QInputDialog.DialogCode.Accepted:
            text = line_edit.text()
            return text, True
        else:
            return None, False
            
    def crear_organigrama(self):
        nombre, ok = self.getText(
            "Crear Organigrama", 
            "Ingrese el nombre de la organización:", 
            regex=OrganigramaRegex.patrones['organizacion'])
        if ok and nombre:
            dialog = DateInputDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                fecha = dialog.getDate()
                self.crearOrganigrama(nombre, fecha)

    def abrir_organigrama(self):
        # Dialogo de abrir archivo
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Archivos de Organigrama (*.org)")
        file_dialog.setDefaultSuffix("org")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                # Perform operations with the selected file
                self.abrirOrganigrama(file_path)
    
    def guardar_organigrama(self):
        # Si el archivo enfocado ya tiene una ruta de guardado, simplemente guardar
        if self.archivoEnfocado.ruta:
            self.guardarOrganigrama(self.archivoEnfocado)
        # Si no abrir menu de guardar como
        else:
            self.guardar_organigrama_como()
    
    def guardar_organigrama_como(self):
        self.guardarOrganigramaComo()
        pass

    def copiar_organigrama(self):
        pass

    def crear_dependencia(self):
        pass

    def eliminar_dependencia(self):
        pass

    def modificar_dependencia(self):
        pass

    def editar_ubicacion_dependencias(self):
        pass

    def ingresar_personas(self):
        pass

    def eliminar_personas(self):
        pass

    def modificar_personas(self):
        pass

    def asignar_personas_dependencias(self):
        pass        

    def personal_por_dependencia(self):
        Informes.salarioPorDependenciaExtendido(self.archivoEnfocado)
        pass

    def personal_por_dependencia_extendido(self):
        pass

    def salario_por_dependencia(self):
        pass

    def salario_por_dependencia_extendido(self):
        pass

    def imprimir_organigrama(self):
        pass

    def graficar_organigrama(self):
        pass


    
        

if __name__ == '__main__':
    app = QApplication([])
    window = EditorDeOrganigramas()
    window.showMaximized()
    app.exec()


