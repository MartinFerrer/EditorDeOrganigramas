from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *

# TODO: Implementar correctamente/completamente
class Archivo(Dependencia):

    Dependencia_keys = {}
    """Un diccionario relacionando a los objetos de Dependencia con su codigo de 3 digitos"""

    Persona_keys = {}
    """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""

    def __init__(self) -> None:
        self.organigrama = Organigrama()
        """Informacion acerca del organigrama"""

        self.raiz = NodoArbol()
        """Primer nodo del organigrama"""

        

    @classmethod
    def genera_code_dependencia(cls): #Genera codigo de dependencia y verifica que no exista.
        while True:
            code = randint(0, 999)
            if code < 10:
                code = "00" + str(code)
            elif code >= 10 and code < 100:
                code = "0" + str(code)
            else:
                code = str(code)
            if code not in cls.Dependencia_keys:
                return code
            
    @classmethod
    def genera_code_dependencia(cls): #Genera codigo de persona y verifica que no exista.
        while True:
            code = randint(0, 9999)
            if code < 10:
                code = "000" + str(code)
            elif code >= 10 and code < 100:
                code = "00" + str(code)
            elif code >= 100 and code < 1000:
                code = "0" + str(code)
            else:
                code = str(code)
            if code not in cls.Persona_keys:
                return code
    
    # TODO: Relacionar el codigo generado al atributo "Codigo" de cada objeto
    

    

    
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



        
