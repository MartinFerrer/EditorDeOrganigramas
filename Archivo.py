from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *

# TODO: Implementar correctamente/completamente
class Archivo(Dependencia):
    
    def __init__(self) -> None:
        self.organigrama = Organigrama()
        """Informacion acerca del organigrama"""

        self.raiz = NodoArbol()
        """Primer nodo del organigrama"""

        self.Personas_keys = {}
        """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""

        self.Dependencia_keys = {}
        """Un diccionario relacionando a los objetos de Dependencia con su codigo de 3 digitos"""

    @staticmethod
    def valida_code_dependencia(self):
        while True:
            self.codigo = super().genera_code()
            if self.codigo not in self.Dependencia_keys:
                break
            pass
    

    
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



        
