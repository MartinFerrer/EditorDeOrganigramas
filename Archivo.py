from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *

# TODO: Implementar correctamente/completamente
class Archivo():
    
    def __init__(self) -> None:
        self.organigrama = Organigrama()
        """Informacion acerca del organigrama"""
        self.raiz = NodoArbol()
        """Primer nodo del organigrama"""
        self.Personas = {}
        """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""
    
     # TODO: Implementar
    def graficarOrganigrama(nodo):
        pass
    
    # TODO: Implementar
    def graficarOrganigramaCompleto(self):
        pass
            
    # TODO: Implementar
    def crearDependencia():
        pass
    
    # TODO: Implementar
    def eliminarDependencia():
        pass
    
    # TODO: Implementar
    def modificarDependencia():
        pass
    
    # TODO: Implementar
    def editarUbicacionDependencia():
        pass
    
    # TODO: Implementar
    def ingresarPersona():
        pass
    
    # TODO: Implementar
    def eliminarPersona():
        pass
    
    # TODO: Implementar
    def modificarPersona():
        pass
    
    # TODO: Implementar
    def asignarPersonaADependencia():
        pass



        
