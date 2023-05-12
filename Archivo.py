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

        self.raiz = NodoArbol(None)

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
            return str(codigo).zfill(3)
        else:
            for i in range(1000):
                codigo = str(i).zfill(3)
                if codigo not in self.dependenciasPorCodigo.keys():
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
                if codigo not in self.personasPorCodigo.keys():
                    return codigo
            raise RuntimeError("No se pudo generar codigo para persona! No hay codigos disponibles.")

    
    # TODO: Relacionar el codigo generado al atributo "Codigo" de cada objeto
    

    
    # TODO: Implementar
    def crearOrganigrama(self):
        pass


    # TODO: Implementar
    def graficarOrganigrama(nodo):
        pass

    
    # TODO: Implementar
    def graficarOrganigramaCompleto(self):
        pass
            
    
    def crearDependencia(self, nom): 
        cod = self.generarCodigoDependencia()
        dep = Dependencia(codigo = cod, codres = None, nombre = nom)
        self.dependenciasPorCodigo[cod] = dep
        

    #Elimina los sucesores de la dependencia "Base" y desasigna a sus trabajadores (Funcion de desasignar esta en la linea 152).
    def eliminarDependencia(self, Base: 'NodoArbol'): 
        for nodo in Base.children:
            self.eliminarDependencia(nodo)
            self.desAsignarPersona(nodo.data.codigo)
            self.dependenciasPorCodigo.pop(nodo.data.codigo)
            Base.children.remove(nodo)
        return

    #Si borrarBase == True, borra el nodo "Base" y sus sucesores, si es False, solamente elimina el nodo "Base" 
    # de los hijos de su antecesor.
    def recorrerNodo(self, Base: 'NodoArbol', Raiz: 'NodoArbol', borrarBase):
        for nodo in Raiz.children:
            if nodo.data.codigo == Base.data.codigo:
                if borrarBase:
                    self.eliminarDependencia(Base)
                    self.desAsignarPersona(nodo.data.codigo)
                    self.dependenciasPorCodigo.pop(nodo.data.codigo)
                Raiz.children.remove(nodo)
            else:
                self.recorrerNodo(Base, nodo, borrarBase)  
   

    
    def modificarDependencia(self, cod_indice, nombre_nuevo, codres_nuevo):
        dep_destino = self.dependenciasPorCodigo[cod_indice]            
        if codres_nuevo in self.personasPorCodigo.keys():
            self.personasPorCodigo[codres_nuevo].dependencia = dep_destino.codigo
            dep_destino.codigoResponsable = codres_nuevo
        if nombre_nuevo != None: 
            dep_destino.nombre = nombre_nuevo

    #Agrega en los hijos de nodoDestino el objeto nodoMover y elimina de los hijos del anterior padre.
    def editarUbicacionDependencia(self, Raiz: 'NodoArbol', nodoMover: 'NodoArbol', nodoDestino: 'NodoArbol'):
        nodoDestino.children.append(nodoMover)
        self.recorrerNodo(nodoMover, Raiz, False)


    
    
    def ingresarPersona(self, nom, ape, ci, tel, dir, salario):
        cod = self.generarCodigoPersona()
        persona = Persona(codigo = cod, nombre = nom, apellido = ape, documento = ci, telefono = tel, direccion = dir, salario = salario)
        self.personasPorCodigo[cod] = persona
        

 
    def eliminarPersona(self, cod_indice):
        for elem in self.dependenciasPorCodigo.values():
            if elem.codigoResponsable == cod_indice:
                elem.codigoResponsable = None
                break
        self.personasPorCodigo.pop(cod_indice)
        

  
    def modificarPersona(self, persona_nueva : Persona):
        persona_destino = self.personasPorCodigo[persona_nueva.codigo]
        persona_destino.dependencia = persona_nueva.dependencia
        persona_destino.nombre = persona_nueva.nombre
        persona_destino.apellido = persona_nueva.apellido
        persona_destino.telefono = persona_nueva.telefono
        persona_destino.direccion = persona_nueva.direccion
        persona_destino.salario = persona_nueva.salario
        
    
  
    def asignarPersonaADependencia(self, cod_persona, dependenciaAsignada):
        persona = self.personasPorCodigo[cod_persona]
        persona.dependencia = dependenciaAsignada
        


    def desAsignarPersona(self, codigo):
        for elem in self.personasPorCodigo.values():
                if elem.dependencia == codigo:
                    elem.dependencia = None
                    elem.salario = 0
        

