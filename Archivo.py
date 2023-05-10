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
        if self.codigoDependenciaMasAlto != 999:
            codigo = self.codigoDependenciaMasAlto + 1
            self.codigoDependenciaMasAlto = codigo
            return str(codigo).zfill(4)
        else:
            for i in range(1000):
                codigo = str(i).zfill(4)
                if codigo not in self.dependenciasPorCodigo.keys:
                    return codigo
            raise RuntimeError("No se pudo generar codigo para dependencia! No hay codigos disponibles.")



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
    def crearDependencia(self, nom):
        cod = self.generarCodigoDependencia()
        dep = Dependencia(codigo = cod, codres = None, nombre = nom)
        self.dependenciasPorCodigo[cod] = dep
        pass
    
    # TODO: Implementar
    def eliminarDependencia():
        pass
    
    # TODO: Implementar
    def modificarDependencia(self, cod_indice, nombre_nuevo, codres_nuevo):
        # No sé si hace falta los ifs?
        # if codres_nuevo in self.personasPorCodigo:
            # if cod_indice in self.dependenciasPorCodigo:
                codres_nuevo = codres_nuevo.zfill(4)
                dep_destino = self.dependenciasPorCodigo[cod_indice]            
                if codres_nuevo in self.personasPorCodigo:
                    self.personasPorCodigo[codres_nuevo].dependencia = dep_destino.codigo
                    dep_destino.codigoResponsable = codres_nuevo
                if nombre_nuevo != None: 
                    dep_destino.nombre = nombre_nuevo
                pass
    
    # TODO: Implementar
    def editarUbicacionDependencia():
        pass
    
    # TODO: Implementar
    def ingresarPersona(self, nom):
        cod = self.generarCodigoPersona()
        persona = Persona(codigo = cod, nombre = nom)
        self.personasPorCodigo[cod] = persona
        pass
    
    # TODO: Implementar
    def eliminarPersona():
        pass
    
    # TODO: Implementar
    def modificarPersona(self, persona_nueva : Persona):
        persona_destino = self.personasPorCodigo[persona_nueva.codigo]
        persona_destino.dependencia = persona_nueva.dependencia
        persona_destino.nombre = persona_nueva.nombre
        persona_destino.apellido = persona_nueva.apellido
        persona_destino.telefono = persona_nueva.telefono
        persona_destino.direccion = persona_nueva.direccion
        persona_destino.salario = persona_nueva.salario
        pass
    
    # TODO: Implementar
    def asignarPersonaADependencia(self):
        pass
