from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton
from PyQt6.QtGui import QFont
import pickle, pickletools

from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *

class EditorDeOrganigramas(QMainWindow):
    
    def __init__(self):
        super().__init__()
        # Set the window title and size
        self.setWindowTitle("Editor De Organigramas")
        self.setGeometry(100, 100, 400, 200)
     
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
        print("Arbol guardado:\n")
        #TODO: segmentar guardado de archivos
        with open('arbol.dat', 'wb') as outf:
            pickled = pickle.dumps(raiz, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

        with open('arbol.dat', 'rb') as inf:
            raiz = pickle.load(inf)
            imprimir_arbol(raiz)
        


        # Create the widgets
        self.label = QLabel("Nombre de organigrama:", self)
        self.label.move(20, 20)
        self.label.adjustSize()
 
        self.line_edit = QLineEdit(self)
        self.line_edit.move(200, 20)
 
        self.button = QPushButton("Crear", self)
        self.button.move(140, 70)
 
        self.result_label = QLabel(self)
        self.result_label.setGeometry(30,80, 200,200)
 
 
        # Connect the button to a method
        self.button.clicked.connect(self.handle_button_click)
 
    def handle_button_click(self):
        text = self.line_edit.text()
        self.result_label.setText(f"Se creo organigrama: {text}!")
        self.result_label.setFont(QFont("Times", 15))
        self.result_label.setStyleSheet('color:red')
    
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
    window.show()
    app.exec()
