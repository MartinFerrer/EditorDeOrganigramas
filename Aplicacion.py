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
    QSizePolicy)
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize
from PyQt6.QtGui import QFont, QAction, QMouseEvent
import pickle, pickletools

from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *
from Archivo import *

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



class EditorDeOrganigramas(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.central_widget = QTextEdit()
        self.init_ui()
        
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

        nieto_1 = NodoArbol(Dependencia(codigo='004', codigoResponsable='3456', nombre='Dependencia D'))
        nieto_2 = NodoArbol(Dependencia(codigo='005', codigoResponsable='7890', nombre='Dependencia E'))

        raiz.agregar_hijo(hijo_1)
        raiz.agregar_hijo(hijo_2)

        hijo_1.agregar_hijo(nieto_1)
        hijo_1.agregar_hijo(nieto_2)

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
