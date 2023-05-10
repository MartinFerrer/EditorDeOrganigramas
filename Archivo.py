from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *
from random import randint

# TODO: Implementar correctamente/completamente
class Archivo():

    def __init__(self) -> None:
        self.organigrama = Organigrama()
        """Informacion acerca del organigrama"""

        self.raiz = NodoArbol()

        self.dependenciasPorCodigo = {}
        """Un diccionario relacionando a los objetos de Dependencia con su codigo de 3 digitos"""

        self.personasPorCodigo = {}
        """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""

        self.codigoPersonaMasAlto = -1
        self.codigoDependenciaMasAlto = -1

        

    
    def generarCodigoDependencia(self): #Genera codigo de dependencia y verifica que no exista.
        if self.codigoPersonaMasAlto != 999:
            codigo = self.codigoDependenciaMasAlto + 1
            self.codigoDependenciaMasAlto = codigo
            return str(codigo).zfill(4)
        else:
            for i in range(10000):
                codigo = str(i).zfill(4)
                if codigo not in self.dependenciasPorCodigo.keys:
                    return codigo
            raise RuntimeError("No se pudo generar codigo para persona! No hay codigos disponibles.")



    def generarCodigoPersona(self): #Genera codigo de persona y verifica que no exista.
        if self.codigoPersonaMasAlto != 9999:
            codigo = self.codigoPersonaMasAlto + 1
            self.codigoPersonaMasAlto = codigo
            return str(codigo).zfill(4)
        else:
            for i in range(10000):
                codigo = str(i).zfill(4)
                if codigo not in self.personasPorCodigo.keys:
                    return codigo
            raise RuntimeError("No se pudo generar codigo para persona! No hay codigos disponibles.")

    
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
    def ingresarPersona(self, nombre):
        cod = Archivo.genera_code_dependencia()
        persona = Persona(codigo = cod, nombre = nombre)
        self.personasPorCodigo[cod] = persona
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



        
