from functools import partial
import numpy as np
import math
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QLabel, 
    QToolBar,
    QDockWidget,
    QLineEdit, 
    QPushButton,
    QTextEdit,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QHBoxLayout,
    QVBoxLayout,
    QStackedLayout,
    QFrame,
    QStyleFactory)
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QTimer
from PyQt6.QtGui import QFont, QAction, QMouseEvent, QWheelEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, 
    QWidget, QVBoxLayout, 
    QGraphicsScene, QGraphicsView, 
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem)
from PyQt6.QtCore import Qt, QRectF, QEvent
from PyQt6.QtGui import QColor, QPen, QPainter, QPixmap

import pickle, pickletools
import time

from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *
from Archivo import *



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
        
    def update_zoom(self, value):
        zoom_factor = value / 5.0  # Example: Map slider values to zoom factors
        self.resetTransform()  # Reset any previous transformations
        self.scale(zoom_factor, zoom_factor)
        
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
    
    def draw_tree(self):
        self.scene().clear()

        # Calculate the available space
        available_width = self.width()
        available_height = self.height()

        # Set margins
        margin_x = 20
        margin_y = 20

        # Set initial node width and height
        node_width = (available_width - 2 * margin_x) / 5
        node_height = (available_height - 2 * margin_y) / 10
    
        root_x = margin_x - (node_width / 2)
        root_y = margin_y - (node_height / 2)

        level_counts = []  # Number of nodes at each level
        self.calculate_level_counts(self.root, 0, level_counts)  # Calculate the counts recursively
        print(level_counts)
        self.draw_node(self.root, root_x, root_y, node_width, node_height, level_counts, 0)

    def calculate_level_counts(self, node, level, level_counts):
        if level >= len(level_counts):
            level_counts.append(0)
        level_counts[level] += 1

        for child in node.children:
            self.calculate_level_counts(child, level + 1, level_counts)

    def draw_node(self, node: NodoArbol, x, y, width, height, level_counts, current_level):
        rect = QGraphicsRectItem(x, y, width, height)
        rect.setPen(QPen(Qt.GlobalColor.black))
        rect.setBrush(QColor(Qt.GlobalColor.lightGray))
        self.scene().addItem(rect)

        label = QGraphicsTextItem(node.data.nombre, rect)
        label.setDefaultTextColor(QColor(Qt.GlobalColor.black))
       
        # Adjust the font size to fit within the node rectangle
        font = label.font()
        # TODO: opcion en el menu para poner el tamaño de texto maximo deseado
        font.setPointSizeF(width * 1.5 / max(len(node.data.nombre), 1))  # Set initial font size dynamically
        label.setFont(font)
        # Decrease font size until the text fits within the available space or reaches the threshold
        while label.boundingRect().width() > width - 10 or label.boundingRect().height() > height - 10:
            if font.pointSizeF() - 1 > 0:
                font.setPointSizeF(font.pointSizeF() - 1)
                label.setFont(font)
            else:
                break
        if font.pointSizeF() >= 7:
            label.setPos(x + (width - label.boundingRect().width()) / 2, y + (height - label.boundingRect().height()) / 2)
        else:
            # Skip adding the label if the font size is less than 7
            self.scene().removeItem(label)
        
        if node.children:
            # TODO: Remove level_counts, no va servir simplemente, se puede tener 3 nodos en un nivel de varias maneras distintas
            # en algunas se van a solapar nodos y en otros no, en vez deberiamos desplazar dinamicamente o simplemente buscar los 
            # vecinos inmediatos al nodo para ajustar el espacio
            print(current_level, level_counts[current_level + 1])
            children_count = len(node.children)
            children_width = width
            children_height = height
            children_spacing = 50
            children_vertical_spacing = 100

            total_children_width = children_count * children_width + (children_count - 1) * children_spacing
            children_x = x + (width - total_children_width) / 2  # Center the children nodes horizontally
            children_y = y + height + children_vertical_spacing

            for i, child in enumerate(node.children):
                child_x = children_x + (i * (children_width + children_spacing))  # Add spacing between the children nodes
                self.draw_node(child, child_x, children_y, children_width, children_height, level_counts, current_level + 1)

                parent_center = QPointF(x + (width / 2), y + height)
                child_center = QPointF(child_x + (children_width / 2), children_y)

                # Draw vertical line segment from parent to intermediate point
                v_line = QGraphicsLineItem(parent_center.x(), parent_center.y(), parent_center.x(), child_center.y() - children_vertical_spacing / 3)
                v_line.setPen(QPen(Qt.GlobalColor.black))
                self.scene().addItem(v_line)

                # Draw horizontal line segment from intermediate point to child
                h_line = QGraphicsLineItem(parent_center.x(), child_center.y() - children_vertical_spacing / 3, child_center.x(), child_center.y() - children_vertical_spacing / 3)
                h_line.setPen(QPen(Qt.GlobalColor.black))
                self.scene().addItem(h_line)

                # Draw vertical line segment from intermediate point to child
                v_line = QGraphicsLineItem(child_center.x(), child_center.y() - children_vertical_spacing / 3, child_center.x(), child_center.y())
                v_line.setPen(QPen(Qt.GlobalColor.black))
                self.scene().addItem(v_line)

    
    # TODO WORKING CODE 
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
        
    # def draw_node(self, node: NodoArbol, x, y, width, height):
    #     rect = QGraphicsRectItem(x, y, width, height)
    #     rect.setPen(QPen(Qt.GlobalColor.black))
    #     rect.setBrush(QColor(Qt.GlobalColor.lightGray))
    #     self.scene().addItem(rect)

    #     label = QGraphicsTextItem(node.data.nombre, rect)
    #     label.setDefaultTextColor(QColor(Qt.GlobalColor.black))
       
    #     # Adjust the font size to fit within the node rectangle
    #     font = label.font()
    #     # TODO: opcion en el menu para poner el tamaño de texto maximo deseado
    #     font.setPointSizeF(width * 1.5 / max(len(node.data.nombre), 1))  # Set initial font size dynamically
    #     label.setFont(font)
    #     # Decrease font size until the text fits within the available space or reaches the threshold
    #     while label.boundingRect().width() > width - 10 or label.boundingRect().height() > height - 10:
    #         if font.pointSizeF() - 1 > 0:
    #             font.setPointSizeF(font.pointSizeF() - 1)
    #             label.setFont(font)
    #         else:
    #             break
    #     if font.pointSizeF() >= 7:
    #         label.setPos(x + (width - label.boundingRect().width()) / 2, y + (height - label.boundingRect().height()) / 2)
    #     else:
    #         # Skip adding the label if the font size is less than 7
    #         self.scene().removeItem(label)
        
    #     if node.children:
    #         children_count = len(node.children)
    #         children_width = width
    #         children_height = height
    #         children_spacing = 50
    #         children_vertical_spacing = 100

    #         total_children_width = children_count * children_width + (children_count - 1) * children_spacing
    #         children_x = x + (width - total_children_width) / 2  # Center the children nodes horizontally
    #         children_y = y + height + children_vertical_spacing

    #         for i, child in enumerate(node.children):
    #             child_x = children_x + (i * (children_width + children_spacing))  # Add spacing between the children nodes
    #             self.draw_node(child, child_x, children_y, children_width, children_height)

    #             parent_center = QPointF(x + (width / 2), y + height)
    #             child_center = QPointF(child_x + (children_width / 2), children_y)

    #             # Draw vertical line segment from parent to intermediate point
    #             v_line = QGraphicsLineItem(parent_center.x(), parent_center.y(), parent_center.x(), child_center.y() - children_vertical_spacing / 3)
    #             v_line.setPen(QPen(Qt.GlobalColor.black))
    #             self.scene().addItem(v_line)

    #             # Draw horizontal line segment from intermediate point to child
    #             h_line = QGraphicsLineItem(parent_center.x(), child_center.y() - children_vertical_spacing / 3, child_center.x(), child_center.y() - children_vertical_spacing / 3)
    #             h_line.setPen(QPen(Qt.GlobalColor.black))
    #             self.scene().addItem(h_line)

    #             # Draw vertical line segment from intermediate point to child
    #             v_line = QGraphicsLineItem(child_center.x(), child_center.y() - children_vertical_spacing / 3, child_center.x(), child_center.y())
    #             v_line.setPen(QPen(Qt.GlobalColor.black))
    #             self.scene().addItem(v_line)

            
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


class ResizableToolBar(QToolBar):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setMouseTracking(True)
        self.mousePressPos = None
        self.mouseIsPressed = False
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePressPos = event.globalPosition()
            self.mouseIsPressed = True

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouseIsPressed:
            diff = event.globalPosition() - self.mousePressPos
            self.mousePressPos = event.globalPosition()

            new_size = self.size() + QSize(diff.x(), diff.y())
            self.resize(new_size)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseIsPressed = False

        super().mouseReleaseEvent(event)

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
        #print(self.minimum_zoom, self.maximum_zoom, self.middle_zoom, value)
                
        if value <= self.middle_zoom:
            #normalized = (value - self.minimum_zoom) / (self.middle_zoom - self.minimum_zoom)
            #max = (1.0 - self.minimum_zoom / 100)
            #mapped = max - normalized * max 
            #zoom_factor = 1.0 - mapped
            # # mapped = (1.0 - self.minimum_zoom / 100) * (1.0 - (value - self.minimum_zoom) / (self.middle_zoom - self.minimum_zoom))
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

class EditorDeOrganigramas(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        # TEMP Unit tests TODO: REMOVE
        persona = Persona(codigo="1011", dependencia="202", nombre="Juan", apellido = "Perez")
        print(persona)
        print(persona.__repr__())
        persona.salario = 100000000
        persona.codigo = "1233"
        
        #TODO: segmentar guardado de archivos
        with open('data.dat', 'wb') as outf:
            pickled = pickle.dumps(persona, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

        with open('data.dat', 'rb') as inf:
            personaLeida = pickle.load(inf)
            print(personaLeida.__repr__())
        
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
        #hijo_2.agregar_hijo(nieto_3)
        #hijo_2.agregar_hijo(nieto_4)
        hijo_3.agregar_hijo(nieto_5)
        hijo_3.agregar_hijo(nieto_6)
        hijo_3.agregar_hijo(nieto_3)
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
        # print("Nodo encontrado:")
        # encontrado = raiz.buscar_nodo('005', compararCodigo)
        # print(encontrado)
        # print("Padre de encontrado:")
        # print(encontrado.padre(raiz))
        
        self.central_widget = OrganizationalChartWidget(raiz)
        self.init_ui()
        
        QTimer.singleShot(1000, self.saveScreenshot)
        QTimer.singleShot(1000, self.save_chart_as_png)


        
    # def showEvent(self, event):
    #     super().showEvent(event)
    #     print(f"Show event")
    #     self.central_widget.organizational_chart.center_chart()

    # def changeEvent(self, event):
    #     # TODO: puede que no centrar el chart en todo evento?
    #     self.central_widget.organizational_chart.center_chart()

    #     print(f"Event changed {event}")
    #     #if event.type() == QEvent.Type.WindowStateChange:
    #         # if self.isMaximized() or self.windowState() & Qt.WindowState.WindowMaximized:
    #         #     self.central_widget.organizational_chart.center_chart()
    #         #     print("WINDOW MAXIMIZED")
    #         # elif:
    #         #     self.central_widget.organizational_chart.center_chart()
    #         # elif self.windowState() & Qt.WindowState.WindowNoState:
    #         #     self.central_widget.organizational_chart.center_chart()
    #     super().changeEvent(event)
    
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
        self.setWindowTitle("Application")
        self.show()
     
    
    def create_toolbar(self):
        self.toolbar = ResizableToolBar("Properties", self)

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

        file_menu = menu_bar.addMenu("File")

        action_open = QAction("Open", self)
        action_save = QAction("Save", self)
        action_exit = QAction("Exit", self)

        file_menu.addAction(action_open)
        file_menu.addAction(action_save)
        file_menu.addAction(action_exit)

        action_open.triggered.connect(self.open_file)
        action_save.triggered.connect(self.save_file)
        action_exit.triggered.connect(self.close)

    def create_status_bar(self):
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        
        self.zoom_widget = ZoomWidget(target_widget=self.central_widget.organizational_chart)
        self.statusBar().addPermanentWidget(self.zoom_widget)

    def set_central_widget(self):
        self.setCentralWidget(self.central_widget)

        self.central_widget.setMouseTracking(True)  # Enable mouse tracking for central widget
        self.central_widget.mouseMoveEvent = self.mouse_move_event
        self.central_widget.mousePressEvent = self.mouse_press_event
        self.central_widget.mouseReleaseEvent = self.mouse_release_event

    def open_file(self):
        # Functionality for opening a file
        pass

    def save_file(self):
        # Functionality for saving a file
        pass

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
        
    # TODO: Implementar
    def crearOrganigrama():
        pass
    
    # TODO: Implementar
    def abrirOrganigrama():
        pass
    
    # TODO: Implementar
    def copiarOrganigrama():
        pass
 
if __name__ == '__main__':
    app = QApplication([])
    window = EditorDeOrganigramas()
    window.showMaximized()
    app.exec()
