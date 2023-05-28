from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton
from PyQt6.QtGui import QFont
import pickle, pickletools
import datetime
import os
import copy

from Entidades.Arbol import *
from Entidades.Persona import *
from Entidades.Dependencia import *
from Archivo import *

class EditorDeOrganigramas(QMainWindow):
    
    def __init__(self):
        super().__init__()
        # Set the window title and size
        self.setWindowTitle("Editor De Organigramas")
        self.setGeometry(100, 100, 400, 200)
        self.archivos = {}
        self.ruta = os.getcwd() + '\Archivos'
        for file in os.listdir(self.ruta):
            dir = self.ruta + '\\' + file
            temp : Archivo = self.leer_archivo(dir, datos = None)
            if temp != None:
                self.archivos[temp.organigrama.codigo] = temp
        
        print(self.archivos)
        print(type(self.archivos))

        persona = Persona(codigo="1011", dependencia="202", nombre="Juan", apellido = "Perez")
        print(persona)
        print(persona.__repr__())
        
        persona.salario = 100000000
        persona.codigo = "1233"  


        fecha = datetime.now()
        self.crearOrganigrama('Hola', fecha)
        print(self.archivos)
        self.crearOrganigrama('Chau', fecha)
        print(self.archivos)
        temp = self.leer_archivo()
        
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
        
        '''lista_temp = ['00001', '00002', '00003']
        with open ('archivos.dat', 'wb') as outcodigof:
            pickled = pickle.dumps(lista_temp, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outcodigof.write(optimized_pickle)

        with open ('archivos.dat', 'rb') as initf:
            lista_nueva = pickle.load(initf)
            print(lista_nueva)
        '''
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
    
    def escribir_archivo (self, nombre_archivo, datos):
        with open (nombre_archivo, 'wb') as outf:
            pickled = pickle.dumps(datos, pickle.HIGHEST_PROTOCOL)
            optimized_pickle = pickletools.optimize(pickled)
            outf.write(optimized_pickle)

    def leer_archivo (self, nombre_archivo, datos):
        with open (nombre_archivo, 'rb') as inf:
            if os.path.getsize(nombre_archivo) != 0:
                datos = pickle.load(inf)
        return datos

    # TODO: Implementar
    def crearCodigoOrganigrama(self):
        cod = 0
        while str(cod).zfill(5) in self.archivos.keys():
            cod += 1
        return str(cod).zfill(5)
    
    def crearOrganigrama(self, nombre, fecha):
        cod = self.crearCodigoOrganigrama()
        nuevo = Archivo()
        nuevo.organigrama.codigo = cod
        nuevo.organigrama.organizacion = nombre
        nuevo.organigrama.fecha = fecha
        self.archivos[str(cod).zfill(5)] = nuevo
        nombre_archivo = self.ruta + '\org_' + nuevo.organigrama.codigo + '.dat'
        print(nombre_archivo)
        self.escribir_archivo(nombre_archivo, nuevo)
    
    # TODO: Implementar
    def abrirOrganigrama():

        pass
    
    # TODO: Implementar
    def copiarOrganigrama(self, codigoOrg, nombre, fecha):
        orgCopy : Archivo = copy.deepcopy(self.archivos[codigoOrg])
        orgCopy.organigrama.codigo = self.crearCodigoOrganigrama()
        orgCopy.personasPorCodigo = {}
        orgCopy.quitarCodres(orgCopy.raiz)
        pass

if __name__ == '__main__':
    app = QApplication([])
    window = EditorDeOrganigramas()
    window.show()   
    app.exec()