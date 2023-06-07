import math
import os
import platform
import copy
import datetime
import pickle
import pickletools
import pprint

import numpy as np
import graphviz

from functools import partial
from PyQt6.QtCore import (
    Qt, QPoint, QPointF, QSize, QTimer, QDate, pyqtSignal, QLocale, QRegularExpression, QUrl,
    QFile, QMargins, QVariant)
from PyQt6.QtGui import (
    QAction, QMouseEvent, QWheelEvent, QIcon, QFont, QColor, QPen, QPainter, QPixmap, QImage, 
    QRegularExpressionValidator, QValidator, QIntValidator, QCloseEvent, QDesktopServices, QPageSize, QCursor
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QToolBar, QDockWidget, QLineEdit, QPushButton, QTextEdit,
    QSplitter, QWidget, QVBoxLayout, QSizePolicy, QSlider, QSpacerItem, QHBoxLayout, QStackedLayout,
    QFrame, QStyleFactory, QMenu, QMessageBox, QInputDialog, QDateEdit, QCalendarWidget, QDialog,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPixmapItem, QDialogButtonBox,
    QTabBar, QTabWidget, QFileDialog, QApplication, QScrollArea, QComboBox, QListWidget, QListWidgetItem
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog


from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *
from Archivo import *
from Informes import *

from typing import Tuple
import fitz
import subprocess
from win32 import win32print, win32api

class OrganizationalChartView(QGraphicsView):
    def __init__(self, archivo: Archivo, raiz: NodoArbol):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.archivo = archivo
        self.raiz = raiz

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


    def draw_tree_to_pdf(self, raiz: NodoArbol, file_path: str) -> str:
        # Generar el grafo con GraphViz
        dot = graphviz.Digraph(format='pdf')
        self.draw_node(dot, raiz)

        dot.graph_attr.update(
            splines='ortho', 
            rankdir='TB',
            fontname='helvetica')
    
        dot.render(filename=file_path, cleanup=True)
        return file_path + ".pdf"


    # TODO: hacer que las flechas se comporten 100% como un organigrama
    def draw_tree(self):
        self.scene().clear()
        
        if not self.archivo:
            return

        # Generar el grafo con GraphViz
        dot = graphviz.Digraph(format='svg')
        self.draw_node(dot, self.raiz)

        dot.graph_attr.update(
            #layout='dot',
            splines='ortho', 
            rankdir='TB',
            fontname='helvetica')
    
        # Renderizar el grafo como SVG y dibujarlo en la QGraphicsScene del widget
        svg_item = QGraphicsSvgItem()
        svg_renderer = QSvgRenderer(dot.pipe())
        svg_item.setSharedRenderer(svg_renderer)
        self.scene().addItem(svg_item)
        
    def draw_node(self, dot : graphviz.Digraph, node: NodoArbol):
        if node is None:
            return

        # Add the node to the graph
        
        # TODO: dibujar mejor los jefes
        nombre, apellido= "Sin", "Jefe"
        jefe = None
        if node.data:
            jefe : Persona = self.archivo.personasPorCodigo.get(node.data.codigoResponsable)
        if jefe:
            nombre = jefe.nombre
            apellido = jefe.apellido
        # TODO arreglar
        tituloNodo = f"{node.data}"
        if node.data is not None:
            tituloNodo = f"{node.data}({node.data.codigo})"
        dot.node(str(id(node)), label=f"{tituloNodo}\n Jefe: {nombre}, {apellido}", shape="rectangle")

        # Recursively add nodes for each child node
        for child in node.children:
            self.draw_node(dot, child)
            # Add the edge from the parent to the child
            dot.edge(str(id(node)), str(id(child)), arrowhead='none', arrowtail='none', dir='none')
              
class OrganizationalChartWidget(QWidget):
    def __init__(self, archivo: Archivo, raiz: NodoArbol):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.archivo = archivo
        self.raiz = raiz
        self.organizational_chart = OrganizationalChartView(archivo, raiz)
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
        self.zoom_slider.setValue(int(new_zoom_value))

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
        calendar_widget.setLocale(QLocale.system())
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

class SelecionDeDependenciaDialog(QDialog):
    NodoArbolRole = Qt.ItemDataRole.UserRole + 1  # Custom role for storing persona object
    
    def __init__(self, root_node: NodoArbol, nodos_a_excluir: list[NodoArbol] = [], titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(250)
        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.populate_list(root_node, nodos_a_excluir)
        self.layout.addWidget(self.list_widget)

        self.button = QPushButton("Select")
        self.button.clicked.connect(self.accept)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

    def populate_list(self, node: NodoArbol, nodos_a_excluir: list[NodoArbol]):
        if node not in nodos_a_excluir:
            list_item = QListWidgetItem(node.data.nombre)
            list_item.setData(self.NodoArbolRole, node)  # Set the node reference as data
            self.list_widget.addItem(list_item)
            for child in node.children:
                self.populate_list(child, nodos_a_excluir)

    def selected_node(self) -> NodoArbol:
        selected_list_item = self.list_widget.currentItem()
        return selected_list_item.data(self.NodoArbolRole)

class DatosPersonaDialog(QDialog):
    def __init__(self, persona:Persona = None, titulo = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Persona")
        self.layout = QVBoxLayout(self)
        
        self.inputs: dict[str, QLineEdit] = {}
        self.error_labels: dict[str, QLabel] = {}

        for prop, (regex, error_message) in PersonaRegex.patrones.items():
            if prop == "codigo" or prop == "dependencia":
                continue

            label = QLabel(prop.capitalize() + ":")
            self.layout.addWidget(label)

            input_field = QLineEdit()
            self.layout.addWidget(input_field)
            self.inputs[prop] = input_field

            validator = QRegularExpressionValidator(QRegularExpression(regex), self)
            input_field.setValidator(validator)

            error_label = QLabel(self)
            error_label.setStyleSheet("color: red")
            error_label.setText(error_message)
            error_label.setVisible(False)
            self.layout.addWidget(error_label)
            self.error_labels[prop] = error_label

            def update_error_label():
                input_field: QLineEdit = self.sender()
                prop = next(key for key, value in self.inputs.items() if value is input_field)
                error_label = self.error_labels[prop]
                if input_field.hasAcceptableInput():
                    error_label.setVisible(False)
                else:
                    error_label.setVisible(True)

            input_field.inputRejected.connect(update_error_label)
            input_field.textChanged.connect(update_error_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        if persona is not None:
            self.fill_input_fields(persona)

    def fill_input_fields(self, persona: Persona):
        for prop, input_field in self.inputs.items():
            if hasattr(persona, prop):
                value = getattr(persona, prop)
                if value is not None:
                    input_field.setText(str(value))
                
    def get_persona(self):
            datos_persona = {}
            for propiedad, input_field in self.inputs.items():
                valor = input_field.text()
                if propiedad == "salario":
                    if valor == "":
                        valor = 0
                    else:
                        valor = int(valor)  # Convertir entrada de salario a entero
                datos_persona[propiedad] = valor

            persona = Persona(**datos_persona) # Pasar todas las propiedades como argumento de constructor
            return persona
 
class PersonaSelectionDialog(QDialog):
    PersonaRole = Qt.ItemDataRole.UserRole + 1  # Custom role for storing persona object

    def __init__(self, personas : list[Persona], titulo: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        layout = QVBoxLayout(self)

        self.personas_list = QListWidget(self)
        layout.addWidget(self.personas_list)

        for persona in personas:
            item = QListWidgetItem(f"{persona.nombre} {persona.apellido}")
            item.setData(self.PersonaRole, QVariant(persona))
            self.personas_list.addItem(item)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_persona_seleccionada(self) -> Persona:
        selected_item = self.personas_list.currentItem()
        if selected_item:
            return selected_item.data(self.PersonaRole)
        else:
            return None
    
class PDFPopupWindow(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualizador de PDF")
        self.pdf_path = pdf_path
        
        layout = QVBoxLayout()
        self.setLayout(layout)
            
        # No permitir cambiar el tamaño de la ventana popup
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.MSWindowsFixedSizeDialogHint) 
        self.pdf_path = pdf_path

        # Create a QScrollArea to display the PDF content
        scroll_area = QScrollArea()
        layout.addWidget(scroll_area)

        # Create a QWidget to contain the rendered PDF pages
        pdf_widget = QWidget()
        pdf_layout = QVBoxLayout()
        pdf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pdf_widget.setLayout(pdf_layout)
        scroll_area.setWidget(pdf_widget)

        # Load and display the PDF content
        pdf_doc: fitz.Document = fitz.open(self.pdf_path)
        for page_num in range(pdf_doc.page_count):
            page: fitz.Page = pdf_doc.load_page(page_num)
            pix: fitz.Pixmap = page.get_pixmap()

            # Convert the pixmap to a QImage
            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

            # Create a QLabel to display the page image
            page_label = QLabel()
            page_label.setPixmap(QPixmap.fromImage(qimage))
            pdf_layout.addWidget(page_label)

        # Enable scrolling within the QScrollArea
        scroll_area.setWidgetResizable(True)

        # Create a QHBoxLayout for the buttons
        button_layout = QHBoxLayout()

        # Create a button for printing the PDF
        print_button = QPushButton("Print PDF")
        print_button.clicked.connect(self.print_pdf)
        button_layout.addWidget(print_button)

        # Create a button for saving the PDF
        save_button = QPushButton("Save PDF")
        save_button.clicked.connect(self.save_pdf)
        button_layout.addWidget(save_button)

        # Create a button for closing the window
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)
        
        # Calculate the desired size based on the content
        desired_width = min(layout.sizeHint().width() + 100, self.parentWidget().width() // 2)
        desired_height = min(layout.sizeHint().height() + 200, self.parentWidget().height() // 2)
        self.resize(desired_width, desired_height)

    # TODO:fix
    def print_pdf(self):
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            #try:
                #os.startfile(self.pdf_path, "print")
            printer_name = print_dialog.printer().printerName()
            page_range = print_dialog.printer().pageRanges().firstPage(), print_dialog.printer().pageRanges().lastPage()
            
            print("PRINTER:")
            print(printer_name)
            print(page_range)
            
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
            print(print_parameters)
            # Print the PDF file
            win32api.ShellExecute(
                0,                  #hwnd
                "printto",            #op
                self.pdf_path,      #file
                print_parameters,   #params
                None,               #_dir
                0                   #bShow
            )
            #except BaseException:
            #    print("Error occurred while printing the PDF.")
            
    def save_pdf(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix(".pdf")
        file_path, _ = file_dialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file_path:
            QFile.copy(self.pdf_path, file_path)

               
class EditorDeOrganigramas(QMainWindow):
    @property
    def archivoEnfocado(self):
        return self._archivoEnfocado

    @archivoEnfocado.setter
    def archivoEnfocado(self, value : Archivo):
        self._archivoEnfocado = value
        self.refrescarVisualizacionOrganigrama(value)

    # TODO: mover
    def refrescarVisualizacionOrganigrama(self, archivo: Archivo, raiz: NodoArbol = None):
        if self.ui_inicializada:
            chart = self.central_widget.organizational_chart
            chart.archivo = archivo
            if raiz is None:
                chart.raiz = archivo.raiz
            else:
                chart.raiz = raiz
            chart.draw_tree()
            chart.center_chart()
            self.update_toolbar()
            print(archivo.organigrama.fecha)
            self.status_label.setText(f"Vigente hasta: {archivo.organigrama.fecha.strftime(r'%d/%m/%Y')}")
            
    def __init__(self):
        super().__init__()
        
        self.ui_inicializada = False
        # Cargar archivos 
        self.archivos : dict[str, Archivo] = {}
        """Diccionario de archivos en memoria con codigo de archivo como llave""" 

        self.directorio_de_trabajo = os.getcwd()
        self.ruta_archivos = os.path.join(self.directorio_de_trabajo, ".Archivos")
        """Ruta donde se guardan archivos internos del programa, incluyendo los archivos de autoguardado/recuperacion"""
        self.ruta_archivos_recientes = os.path.join(self.ruta_archivos, "archivos_recientes.dat")
        
        self.informador = Informador(self.ruta_archivos)
        """Instancia de clase para generar los informes"""
        
        self.archivoEnfocado = Archivo()
        self.archivoEnfocado.ruta = os.path.join(self.ruta_archivos, "00000.org")
        print(self.archivoEnfocado.ruta)
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
            
            

        persona = Persona(codigo="1011", dependencia="202", nombre="Juan", apellido = "Perez")
        print(persona)
        print(persona.__repr__())
        persona.salario = 100000000
        persona.codigo = "1233"  


        temp = self.archivoEnfocado
        print("\n\n\n")
        print(temp.raiz)
        temp.crearDependencia("Gotocesars", temp.raiz)
        print(self.archivoEnfocado.raiz)
        print("Test\n\n\n\n\n\n\n")
        dep = temp.raiz.buscar_nodo("000", NodoArbol.compararCodigo)
        print(dep)
        temp.ingresarPersona(Persona(nombre="Fabri", apellido="Kawabata", documento="5406655", telefono="0972399578", direccion="Angel Torres", salario=1234))
        temp.ingresarPersona(Persona(nombre="Hiroto", apellido="Yamashita", documento="2348932", telefono="2384123", direccion="Mcal. Estigarribia", salario=2345))
        temp.asignarPersonaADependencia("0000", "000")
        temp.modificarDependencia(codigoDependencia="000", codresNuevo="0000")
        individuo = temp.personasPorCodigo["0000"]
        print(individuo)
        print(temp.raiz.data)
        temp.raiz.recorrer_arbol(NodoArbol.quitarJefe, "0000")
        print(temp.raiz.data)
        temp.modificarDependencia(codigoDependencia="000", codresNuevo="0001")
        print(temp.raiz.data)

    
        # Crear el árbol
        
        raiz = NodoArbol(Dependencia(codigo='001', codigoResponsable='1011', nombre='Dependencia A'))
        
        hijo_1 = NodoArbol(Dependencia(codigo='002', codigoResponsable='1012', nombre='Dependencia B'))
        hijo_2 = NodoArbol(Dependencia(codigo='003', codigoResponsable='1013', nombre='Dependencia C'))
        hijo_3 = NodoArbol(Dependencia(codigo='006', codigoResponsable='1014', nombre='Dependencia F'))

        nieto_1 = NodoArbol(Dependencia(codigo='004', codigoResponsable='1015', nombre='Dependencia D'))
        nieto_2 = NodoArbol(Dependencia(codigo='005', codigoResponsable='1016', nombre='Dependencia E'))
        nieto_3 = NodoArbol(Dependencia(codigo='007', codigoResponsable='1017', nombre='Dependencia G'))
        nieto_4 = NodoArbol(Dependencia(codigo='008', codigoResponsable='1018', nombre='Dependencia H'))
        nieto_5 = NodoArbol(Dependencia(codigo='009', codigoResponsable='1019', nombre='Dependencia I'))
        nieto_6 = NodoArbol(Dependencia(codigo='010', codigoResponsable='1020', nombre='Dependencia J'))


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

        archivo : Archivo = Archivo()
        archivo.organigrama.organizacion = "OrgPrueba"
        archivo.organigrama.fecha = datetime.now()
        archivo.raiz = raiz
        archivo.codigosDeDependencias = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']
        
        def compararCodigo(nodo : NodoArbol, codigo):
            return nodo.data.codigo == codigo
        
        print("Nodo encontrado:")
        encontrado = raiz.buscar_nodo('005', compararCodigo)
        print(encontrado)
        print("Padre de encontrado:")
        print(encontrado.padre(raiz))


        persona1 = Persona(codigo="1011", dependencia="001", nombre="Juan", apellido = "Perez", salario=50000)
        persona2 = Persona(codigo="1012", dependencia="002", nombre="Pedro", apellido = "Pascal", salario=565656)
        persona3 = Persona(codigo="1013", dependencia="003", nombre="Poroto", apellido = "Manteca", salario=636363)
        persona4 = Persona(codigo="1014", dependencia="004", nombre="El", apellido = "Ivan", salario=5959595)
        persona5 = Persona(codigo="1015", dependencia="005", nombre="Fabrizio", apellido = "K", salario=200000)
        persona6 = Persona(codigo="1016", dependencia="006", nombre="Martin", apellido = "F", salario=19191919)
        persona7 = Persona(codigo="1017", dependencia="007", nombre="Javier", apellido = "G", salario=666666)
        persona8 = Persona(codigo="1018", dependencia="008", nombre="Filippi", apellido = "Profe", salario=100000)
        persona9 = Persona(codigo="1019", dependencia="009", nombre="Ivan", apellido = "Aux", salario=10000)
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
        
        # DEBUG
        print("\n\n\n\n\n\n\n")
        print("Dependencias por codigo")
        print(archivo.codigosDeDependencias)
        
        print("Archivo guardado:\n")
        with open('archivo.org', 'wb') as outf:
            pickled = pickle.dumps(archivo, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

        with open('archivo.org', 'rb') as inf:
            archivo = pickle.load(inf)
            imprimir_arbol(archivo.raiz)
        
        # Informes    
        self.informador.personalPorDependencia(self.archivoEnfocado, hijo_1.data)
        self.informador.salarioPorDependencia(self.archivoEnfocado, hijo_1.data)
        self.informador.salarioPorDependenciaExtendido(self.archivoEnfocado, raiz)
        self.informador.personalPorDependenciaExtendido(self.archivoEnfocado, hijo_1)

        # Application setup
        # Set the window title and size
        self.setWindowTitle("Editor De Organigramas")
        self.setGeometry(100, 100, 400, 200)
        
        self.central_widget = OrganizationalChartWidget(self.archivoEnfocado, self.archivoEnfocado.raiz)
        self.init_ui()
        self.ui_inicializada = True
        print(self.archivoEnfocado.ruta)

         
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
        self.setWindowIcon(QIcon(".\Icono.ico"))
        self.show()
     
    def create_toolbar(self):
        # Create the toolbar
        self.toolbar = QToolBar("Personas", self)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setOrientation(Qt.Orientation.Vertical)

        # Create a scrollable area for the personas widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Create a widget to hold the personas
        self.personas_widget = QWidget()
        self.personas_layout = QVBoxLayout(self.personas_widget)
        self.personas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.personas_layout.setSpacing(0)  # Set spacing between persona buttons to 0  
        self.scroll_area.setWidget(self.personas_widget)
        
        # Add a label to display the title and count of personas
        self.personas_count_label = QLabel(f"Personas ({len(self.archivoEnfocado.personasPorCodigo)})")
        self.personas_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.personas_count_label.font()
        font.setPointSize(11)  # Set the desired font size
        self.personas_count_label.setFont(font)
        self.personas_count_label.setContentsMargins(0, 0, 4, 4)
        self.toolbar.addWidget(self.personas_count_label)
        
        # Add the scroll area to the toolbar
        self.toolbar.addWidget(self.scroll_area)

        # Add the toolbar to the right toolbar area
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, self.toolbar)
        
        # Crear el menu contextual para el click derecho a las personas
        self.context_menu = QMenu(self)

        # Add actions to the context menu
        eliminarPersona = QAction("Eliminar Persona", self)
        modificarPersona = QAction("Modificar Persona", self)
        asignarPersona = QAction("Asignar Persona a Dependencia", self)

        self.context_menu.addAction(eliminarPersona)
        self.context_menu.addAction(modificarPersona)
        self.context_menu.addAction(asignarPersona)

        # Connect actions to their respective slots
        eliminarPersona.triggered.connect(self.contextual_eliminar_persona)
        modificarPersona.triggered.connect(self.contextual_modificar_persona)
        asignarPersona.triggered.connect(self.contextual_asignar_persona)

        # Add a button to call ingresar_personas
        ingresar_button = QAction("＋ Ingresar Persona", self)
        ingresar_button.triggered.connect(self.ingresar_personas)
        self.toolbar.addAction(ingresar_button)

        # Update the toolbar with initial personas
        self.update_toolbar()
        
        
    def update_toolbar(self):
        # Clear the personas layout
        for i in reversed(range(self.personas_layout.count())):
            self.personas_layout.itemAt(i).widget().setParent(None)

        # Add personas to the personas layout
        for persona in self.archivoEnfocado.personasPorCodigo.values():
            button = QPushButton(f"{persona.nombre} {persona.apellido}")
            button.setProperty("persona", persona)  # Store the persona object as a property of the button
            # Connect the slot function to the button's clicked signal
            button.clicked.connect(self.clikear_persona_en_lista)
            # Contectar el menu contextual
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda event, p=persona: self.show_context_menu(event, p))
            
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
            self.personas_layout.addWidget(button)
       
        # Update the personas count label
        self.personas_count_label.setText(f"Personas ({len(self.archivoEnfocado.personasPorCodigo)})")

        # Update the toolbar
        self.toolbar.update()
        
    def clikear_persona_en_lista(self):
        # Mostrar detalles de la persona
        # Get the button that triggered the slot
        button = self.sender()

        # Retrieve the stored persona object from the button's property
        persona: Persona = button.property("persona")
        if persona:
            # Show the persona details in a message box
            message = (
                f"Nombre: {persona.nombre}\n"
                f"Apellido: {persona.apellido}\n"
                f"Documento: {persona.documento}\n"
                f"Teléfono: {persona.telefono}\n"
                f"Dirección: {persona.direccion}\n"
                f"Salario: {persona.salario}\n"
                f"Dependencia: {self.archivoEnfocado.raiz.buscar_nodo(persona.dependencia, NodoArbol.compararCodigo)}\n"
            )
            QMessageBox.information(self, "Detalles de Persona", message)
   
    def show_context_menu(self, event: QPoint, persona: Persona):
        # Store the selected persona
        self.context_menu_persona = persona

        # Show the context menu at the cursor position
        self.context_menu.exec(QCursor.pos())

    def contextual_eliminar_persona(self):
        self.archivoEnfocado.eliminarPersona(self.context_menu_persona.codigo)
        self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def contextual_modificar_persona(self):
        self.modificar_persona(self.context_menu_persona)

    def contextual_asignar_persona(self):
        self.asignar_persona_a_dependencia(self.context_menu_persona)
            
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
                    ("Cambiar Nombre Organigrama", self.cambiar_nombre_organigrama),
                    ("Cambiar Fecha Organigrama", self.cambiar_fecha_organigrama),
                    ("Copiar Organigrama", self.copiar_organigrama),
                    SEPARADOR_HORIZONTAL,
                    ("Graficar Organigrama Completo", self.graficar_organigrama_completo),
                    ("Graficar Organigrama Por Dependencia", self.graficar_organigrama_por_dependencia),
                    SEPARADOR_HORIZONTAL,
                    ("Crear Dependencia", self.crear_dependencia),
                    ("Eliminar Dependencia", self.eliminar_dependencia),
                    ("Modificar Dependencia", self.modificar_dependencia),
                    ("Editar Ubicacion Dependencias", self.editar_ubicacion_dependencias)
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
                    SEPARADOR_HORIZONTAL,
                    ("Salario por Dependencia", self.salario_por_dependencia),
                    ("Salario por Dependencia Extendido", self.salario_por_dependencia_extendido),
                    SEPARADOR_HORIZONTAL,
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
                    action.triggered.connect(self.graficar_organigrama_completo) # Regraficar el organigrama completo cuando graficamos
                    action.triggered.connect(action_data)
                    menu.addAction(action)

    def actualizar_archivos_recientes(self, submenu: QMenu):
        # Vaciar primero el submenu
        submenu.clear()

        # Obtener los archivos recientes y agregarlos al submenu
        for file_name in self.archivosRecientes:
            action = QAction(file_name, self)
            action.triggered.connect(self.abrir_archivo_reciente)
            submenu.addAction(action)
                
    def abrir_archivo_reciente(self):
        # Obtener texto de la direccion seleccionada
        archivo_seleccionado = self.sender().text()
        # Abrir el archivo que esta en esa direccion
        self.abrirOrganigrama(archivo_seleccionado)
                         
    def create_status_bar(self):
        # Crear un tab bar
        self.tab_bar_archivos = QTabBar(self)
        self.tab_bar_archivos.setTabsClosable(True)
        self.tab_bar_archivos.tabCloseRequested.connect(self.cerrarTabArchivo)
        self.tab_bar_archivos.tabBarClicked.connect(self.clickearTabArchivo)
        self.statusBar().addWidget(self.tab_bar_archivos)
        # Definir un diccionario para guardar los indices de los tabs con el codigo de archivo como llave
        self.tab_indexes = {}
        # Agregar archivo enfocado a los tabs
        tab_index = self.tab_bar_archivos.addTab(self.archivoEnfocado.organigrama.organizacion)
        self.tab_bar_archivos.setCurrentIndex(tab_index)
        self.tab_indexes[self.archivoEnfocado.organigrama.codigo] = tab_index
        
        self.status_label = QLabel(f"Vigente hasta: {self.archivoEnfocado.organigrama.fecha.strftime(r'%d/%m/%Y')}")
        self.statusBar().addWidget(self.status_label)
        
        self.zoom_widget = ZoomWidget(target_widget=self.central_widget.organizational_chart)
        self.statusBar().addPermanentWidget(self.zoom_widget)
        
    def clickearTabArchivo(self, index):
        # Actualizar archivo enfocado cuando cambiamos de tab
        if index != self.tab_indexes[self.archivoEnfocado.organigrama.codigo]:
            codigo_archivo_en_tab = [k for k, v in self.tab_indexes.items() if v == index][0]
            self.archivoEnfocado = self.archivos[codigo_archivo_en_tab]

    def cerrarTabArchivo(self, index_a_cerrar):
            # No cerrar si es el unico archivo abierto
            if len(self.tab_indexes) <= 1:
                error_message = QMessageBox()
                error_message.setIcon(QMessageBox.Icon.Critical)
                error_message.setWindowTitle("Error")
                error_message.setText("No se puede cerrar el unico organigrama abierto!")
                error_message.exec()
                return

            #Obtener el codigo del archivo a cerrar
            codigo_archivo_cerrado = [k for k, v in self.tab_indexes.items() if v == index_a_cerrar][0]
            archivo_cerrado = self.archivos[codigo_archivo_cerrado]
            # Si el archivo no tiene ruta o tubo cambios mostrar el cuadro de diálogo de confirmación de guardado
            if (archivo_cerrado.ruta == "" or archivo_cerrado.modificado):
                result = self.mostrar_confirmacion_guardado(archivo_cerrado)
                if result == QMessageBox.StandardButton.Save:
                    archivoEnfocado = self.archivoEnfocado # Preservar el archivo enfocado anterior
                    self.archivoEnfocado = archivo_cerrado
                    # Si el archivo ya tiene una ruta asociada simplemente guardarlo ahi
                    if archivo_cerrado.ruta:
                        self.guardar_organigrama()
                    # Si el archivo no tiene una ruta asociada debemos pedir la ruta donde guardar
                    else:
                        self.guardar_organigrama_como()
                    self.archivoEnfocado = archivoEnfocado # Reasignar el archivo enfocado preservado
                elif result == QMessageBox.StandardButton.Discard:
                    pass  # No importa, descartar archivo y cerrar el tab
                elif result == QMessageBox.StandardButton.Cancel:
                    return  # Cancelar, no cerrar el tab
            
            # Eliminar el archivo cerrado
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
   
    # Sobreescribir el evento de cerrado para poder guardar cambios que no se han guardado
    def closeEvent(self, event : QCloseEvent):
        archivos_sin_guardar : list[Archivo] = []
        for archivo_code in self.tab_indexes.keys():
            archivo = self.archivos.get(archivo_code)
            # Si el archivo no tiene ruta asociada (nunca fue guardado) o fue modificado sin guardar
            if archivo and (not archivo.ruta or archivo.modificado):
                archivos_sin_guardar.append(archivo)

        if archivos_sin_guardar:
            for archivo in archivos_sin_guardar:
                result = self.mostrar_confirmacion_guardado(archivo)
                if result == QMessageBox.StandardButton.Save:
                    self.archivoEnfocado = archivo
                    # Si el archivo ya tiene una ruta asociada simplemente guardarlo ahi
                    if archivo.ruta:
                        self.guardar_organigrama()
                    # Si el archivo no tiene una ruta asociada debemos pedir la ruta donde guardar
                    else:
                        self.guardar_organigrama_como()
                elif result == QMessageBox.StandardButton.Discard:
                    pass  # Discard changes
                elif result == QMessageBox.StandardButton.Cancel:
                    event.ignore()  # Cancel application close

            if event.isAccepted():
                event.accept()  # Accept application close
        else:
            event.accept()  # Accept application close
 
    def mostrar_confirmacion_guardado(self, archivo):
        """Cuadro de confirmación que pregunta si guardar un archivo, descartar cambios o cancelar la acción"""
        message_box = QMessageBox()
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
     
    def mouse_move_event(self, event):
        # Handle mouse move event
        pos = event.pos()
        # self.status_label.setText(f"Mouse position: ({pos.x()}, {pos.y()})")

    def mouse_press_event(self, event):
        # Handle mouse press event
        pos = event.pos()
        # self.status_label.setText(f"Mouse clicked at: ({pos.x()}, {pos.y()})")

    def mouse_release_event(self, event):
        # Handle mouse release event
        pos = event.pos()
        # self.status_label.setText(f"Mouse released at: ({pos.x()}, {pos.y()})")
        #self.status_label.clear()
        
    def escribir_archivo (self, nombre_archivo, datos) -> None:
        with open (nombre_archivo, 'wb') as outf:
            pickled = pickle.dumps(datos, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

    def leer_archivo (self, nombre_archivo):
        try:
            with open (nombre_archivo, 'rb') as inf:
                if os.path.getsize(nombre_archivo) != 0:
                    datos = pickle.load(inf)
            return datos
        except:
            return None

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
        archivo: Archivo = self.leer_archivo(rutaArchivo)
        if archivo is None:
            QMessageBox.critical(self, "Error", "Error al leer el archivo!")
            return
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
    
    # TODO: implementar autoguardado (Funcion inovadadora)
    def autoGuardadoDeOrganigramas(self):
        pass
    
    def guardarOrganigrama(self, archivo: Archivo):
        if not archivo.ruta:
            raise FileNotFoundError(
                f"El archivo del organigrama '{archivo.organigrama.organizacion}' no tiene una ruta asociada.") 
        else:
            archivo.modificado = False # Se guardan los cambios por lo tanto el archivo no estara modificado
            self.escribir_archivo(archivo.ruta, archivo)
        
    def guardarOrganigramaComo(self, archivo: Archivo, rutaDondeGuardar: str):
        archivo.ruta = rutaDondeGuardar
        self.guardarOrganigrama(archivo)
                
    def copiarOrganigrama(self, archivo: Archivo, organizacion: str, fecha: str):
        orgCopy : Archivo = copy.deepcopy(archivo)
        orgCopy.organigrama.codigo = self.crearCodigoOrganigrama()
        orgCopy.organigrama.organizacion = organizacion
        orgCopy.organigrama.fecha = fecha
        orgCopy.ruta = ""
        orgCopy.modificado = False
        orgCopy.personasPorCodigo = {}
        orgCopy.quitarCodres(orgCopy.raiz)
        self.archivos[orgCopy.organigrama.codigo] = orgCopy
        return orgCopy

    def getText(self, title, message, default = None, regex : Tuple[str, str] = None):
        dialog = QInputDialog(self)
        dialog.setLabelText(message)
        dialog.setWindowTitle(title)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setOkButtonText("Aceptar")
        dialog.setCancelButtonText("Cancelar")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        line_edit: QLineEdit = dialog.findChild(QLineEdit)
        if default:
            line_edit.setText(default)
        if regex:
            validator = QRegularExpressionValidator(QRegularExpression(regex[0]), dialog)
            line_edit.setValidator(validator)
            error_text = f"Valor inválido. {regex[1]}"
            
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
                nuevoArchivo : Archivo = self.crearOrganigrama(nombre, fecha)
                # Enfocar el nuevo archivo
                self.archivoEnfocado = nuevoArchivo     
                # Agregar tab con el nuevo organigrama
                tab_index = self.tab_bar_archivos.addTab(nuevoArchivo.organigrama.organizacion)
                self.tab_bar_archivos.setCurrentIndex(tab_index)
                self.tab_indexes[nuevoArchivo.organigrama.codigo] = tab_index

    def abrir_organigrama(self):
        # Dialogo de abrir archivo
        dialogo_archivo = QFileDialog()
        dialogo_archivo.setNameFilter("Archivos de Organigrama (*.org)")
        dialogo_archivo.setDefaultSuffix("org")
        dialogo_archivo.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if dialogo_archivo.exec() == QFileDialog.DialogCode.Accepted:
            archivos_selecionados = dialogo_archivo.selectedFiles()
            if archivos_selecionados:
                ruta_archivo = archivos_selecionados[0]
                # Perform operations with the selected file
                self.abrirOrganigrama(ruta_archivo)
    
    def guardar_organigrama(self):
        # TODO: remover print
        print(self.archivoEnfocado.ruta)
        # Si el archivo enfocado ya tiene una ruta de guardado, simplemente guardar
        if self.archivoEnfocado.ruta:
            self.guardarOrganigrama(self.archivoEnfocado)
        # Si no abrir menu de guardar como
        else:
            self.guardar_organigrama_como()
    
    def guardar_organigrama_como(self):
        nombre_predenterminado = f"{self.archivoEnfocado.organigrama.organizacion}.org"
        dialogo_archivo = QFileDialog()
        ruta_archivo, _ = dialogo_archivo.getSaveFileName(
            caption="Guardar Organigrama",
            directory=nombre_predenterminado,
            filter="Organigrama Files (*.org)"
        )
        if ruta_archivo:
            self.guardarOrganigramaComo(self.archivoEnfocado, ruta_archivo)

    def cambiar_nombre_organigrama(self):
        nombreNuevo, ok = self.getText(
            "Cambiar Nombre Organigrama", 
            "Ingrese el nuevo nombre para la organización:", 
            regex=OrganigramaRegex.patrones['organizacion'])
        if ok and nombreNuevo:
            self.archivoEnfocado.organigrama.organizacion = nombreNuevo
            # Actualizar nombre de tab
            self.tab_bar_archivos.setTabText(self.tab_bar_archivos.currentIndex(), nombreNuevo)
    
    def cambiar_fecha_organigrama(self):
        dialog = DateInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fecha = dialog.getDate()
            self.archivoEnfocado.organigrama.fecha = fecha
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
    
    def copiar_organigrama(self):
        nombre, ok = self.getText(
        "Copiar Organigrama", 
        "Ingrese el nombre de la organización copiada:", 
        regex=OrganigramaRegex.patrones['organizacion'])
        if ok and nombre:
            dialog = DateInputDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                fecha = dialog.getDate()
                nuevoArchivo : Archivo = self.copiarOrganigrama(self.archivoEnfocado, nombre, fecha)
                # Enfocar el nuevo archivo
                self.archivoEnfocado = nuevoArchivo 
                # Agregar tab con el nuevo organigrama
                tab_index = self.tab_bar_archivos.addTab(nuevoArchivo.organigrama.organizacion)
                self.tab_bar_archivos.setCurrentIndex(tab_index)
                self.tab_indexes[nuevoArchivo.organigrama.codigo] = tab_index

    def crear_dependencia(self):
        nombreDependencia, ok = self.getText(
        "Crear Dependencia", 
        f"Ingrese el nombre para la dependencia:", 
        regex=DependenciaRegex.patrones['nombre'])
        if ok:
            nodo_seleccionado = None
            if self.archivoEnfocado.raiz is not None:
                dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar la dependencia padre:", parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    nodo_seleccionado = dialog.selected_node()
            self.archivoEnfocado.crearDependencia(nombreDependencia, nodo_seleccionado)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
        
    def eliminar_dependencia(self):
        if self.archivoEnfocado.raiz is None:  # Check if there are no options
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama. Ingrese una con CrearDependencia")
            return  # Return without performing any further actions
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar dependencia a eliminar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_seleccionado = dialog.selected_node()
            self.archivoEnfocado.eliminarDependencia(nodo_seleccionado)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def modificar_dependencia(self):
        if self.archivoEnfocado.raiz is None:  # Check if there are no options
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama. Ingrese una con CrearDependencia")
            return  # Return without performing any further actions
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccionar dependencia a modificar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_seleccionado = dialog.selected_node()
            nombreNuevo, ok = self.getText(
            "Modificar Nombre Dependencia", 
            f"Ingrese el nuevo nombre para la dependencia '{nodo_seleccionado.data.nombre}':", 
            default=f'{nodo_seleccionado.data.nombre}',
            regex=DependenciaRegex.patrones['nombre'])
            if ok:
                dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                                titulo="Ingrese el nuevo jefe para la dependencia:", parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    persona_seleccionada = dialog.get_persona_seleccionada()
                    self.archivoEnfocado.modificarDependencia(nodo_seleccionado.data.codigo, nombreNuevo, persona_seleccionada.codigo)
                    self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def editar_ubicacion_dependencias(self):
        if self.archivoEnfocado.raiz is None:  # Check if there are no options
            QMessageBox.critical(self, "Error", "No hay dependencias en el organigrama. Ingrese una con CrearDependencia")
            return  # Return without performing any further actions
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo= "Seleccionar dependencia a mover:", parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_a_mover = dialog.selected_node()
            dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, 
                                                 # Excluimos el nodo a mover y sus hijos ya que no tiene sentido logico
                                                 nodos_a_excluir=[nodo_a_mover],
                                                 titulo="Seleccionar donde ubicar:", 
                                                 parent=self)
            if dialog.list_widget.count() == 0:  # Check if there are no options
                QMessageBox.critical(self, "Error", "No available options.")
                return  # Return without performing any further actions
            if dialog.exec() == QDialog.DialogCode.Accepted:
                nuevo_nodo_padre = dialog.selected_node()   
                if nuevo_nodo_padre is not None:
                    self.archivoEnfocado.editarUbicacionDependencia(nodo_a_mover, nuevo_nodo_padre)
                    self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def ingresar_personas(self):
        dialog = DatosPersonaDialog(titulo="Crear Persona", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            persona = dialog.get_persona()
            self.archivoEnfocado.ingresarPersona(persona)
            self.update_toolbar()

    def eliminar_personas(self):
        dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                        titulo="Persona a Eliminar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            persona_seleccionada = dialog.get_persona_seleccionada()
            if persona_seleccionada:
                codigo_persona = persona_seleccionada.codigo
                self.archivoEnfocado.eliminarPersona(codigo_persona)
                self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def modificar_personas(self):
        dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                titulo="Persona a Modificar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            persona_seleccionada = dialog.get_persona_seleccionada()
            self.modificar_persona(persona_seleccionada)
            
    def modificar_persona(self, persona: Persona):
        dialog = DatosPersonaDialog(persona, titulo="Modificar Persona", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_persona = dialog.get_persona()
            self.archivoEnfocado.modificarPersona(persona.codigo, datos_persona)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def asignar_personas_dependencias(self):
        dialog = PersonaSelectionDialog(self.archivoEnfocado.personasPorCodigo.values(), 
                                titulo="Persona a Asignar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            persona_seleccionada = dialog.get_persona_seleccionada()
            self.asignar_persona_a_dependencia(persona_seleccionada)

    def asignar_persona_a_dependencia(self, persona: Persona):
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo= "Dependencia donde asignar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_a_mover = dialog.selected_node()
            self.archivoEnfocado.asignarPersonaADependencia(persona.codigo, nodo_a_mover.data.codigo)
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)

    def pedir_nodo_para_imprimir_informe(self, funcion):
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, titulo="Seleccion Dependencia para Informe:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_seleccionado = dialog.selected_node()
            rutaPDF = funcion(nodo_seleccionado)
            if rutaPDF:
                pdf_popup = PDFPopupWindow(rutaPDF, parent=self)
                pdf_popup.exec()

    def personal_por_dependencia(self):
        funcion_informe = lambda nodo: self.informador.personalPorDependencia(self.archivoEnfocado, nodo.data)
        self.pedir_nodo_para_imprimir_informe(funcion_informe)

    def personal_por_dependencia_extendido(self):
        funcion_informe = lambda nodo: self.informador.personalPorDependenciaExtendido(self.archivoEnfocado, nodo)
        self.pedir_nodo_para_imprimir_informe(funcion_informe)

    def salario_por_dependencia(self):
        funcion_informe = lambda nodo: self.informador.salarioPorDependencia(self.archivoEnfocado, nodo.data)
        self.pedir_nodo_para_imprimir_informe(funcion_informe)

    def salario_por_dependencia_extendido(self):
        funcion_informe = lambda nodo: self.informador.salarioPorDependenciaExtendido(self.archivoEnfocado, nodo)
        self.pedir_nodo_para_imprimir_informe(funcion_informe)
        
    def imprimir_organigrama(self):
        ruta = os.path.join(self.ruta_archivos, "Grafico_Organigrama")
        funcion_informe = lambda nodo: self.central_widget.organizational_chart.draw_tree_to_pdf(nodo, ruta)
        self.pedir_nodo_para_imprimir_informe(funcion_informe)
              
    def graficar_organigrama_completo(self):
        self.refrescarVisualizacionOrganigrama(self.archivoEnfocado)
        
    def graficar_organigrama_por_dependencia(self):
        dialog = SelecionDeDependenciaDialog(self.archivoEnfocado.raiz, 
                                             titulo="Dependencia a Graficar:", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nodo_a_graficar = dialog.selected_node()
            self.central_widget.organizational_chart.raiz = nodo_a_graficar
            self.refrescarVisualizacionOrganigrama(self.archivoEnfocado, nodo_a_graficar)

if __name__ == '__main__':
    app = QApplication([])
    window = EditorDeOrganigramas()
    window.showMaximized()
    app.exec()
