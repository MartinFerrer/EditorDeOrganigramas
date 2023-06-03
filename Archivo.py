from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *
from random import randint

# TODO: Implementar correctamente/completamente
class Archivo():

    def __init__(self) -> None:
        self.organigrama : Organigrama = Organigrama()
        """Informacion acerca del organigrama"""

        self.raiz : NodoArbol = NodoArbol(None)
        """Raiz del arbol con dependencias que representan al organigrama"""

        self.dependenciasPorCodigo : list[str] = []
        """Un diccionario relacionando a los objetos de Dependencia con su codigo de 3 digitos"""

        self.personasPorCodigo : dict[str, Persona] = {}
        """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""

        self.codigoPersonaMasAlto : int = -1
        self.codigoDependenciaMasAlto : int = -1

        
    def generarCodigoDependencia(self): 
        """Genera codigo de dependencia y verifica que no exista.""" 
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

    def generarCodigoPersona(self):
        """Genera codigo de persona y verifica que no exista.""" 
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
    


    # TODO: Implementar
    def graficarOrganigrama(nodo):
        pass

    
    # TODO: Implementar
    def graficarOrganigramaCompleto(self):
        pass


    def quitarCodres(self, raiz : NodoArbol):
        """Recorre todo el organigrama para poner en None el Codres"""
        raiz.data.codigoResponsable = None
        for nodo in raiz.children:
            self.quitarCodres(nodo)


    def crearDependencia(self, nom, nodoPadre : NodoArbol): 
        cod = self.generarCodigoDependencia()
        dep = Dependencia(codigo = cod, codres = None, nombre = nom)
        nodo = NodoArbol(dep)
        nodoPadre.agregar_hijo(nodo)
        self.dependenciasPorCodigo.append(cod)
        
    def eliminarDependencia(self, codigo_dependencia):
        """Permite eliminar una dependencia existente y todas las 
           dependencias sucesoras de la misma."""
        
        def compararCodigo(nodo : NodoArbol, codigo):
            return nodo.data.codigo == codigo
        nodo = self.raiz.buscar_nodo(codigo_dependencia, compararCodigo) #Retorna el nodo que tiene el codigo indicado en el argumento

        padre : NodoArbol = nodo.padre(self.raiz) #Padre del nodo encontrado
        padre.eliminar_hijo(nodo)
        self.eliminarNodoYSucesores(nodo)

    # Elimina los sucesores de la dependencia "base" y desasigna a sus trabajadores 
    def eliminarNodoYSucesores(self, base: 'NodoArbol'): 
        self.desasignarPersonasDeDependencia(base.data.codigo)
        self.dependenciasPorCodigo.remove(base.data.codigo)
        for nodo in base.children:
            base.children.remove(nodo)
            self.eliminarNodoYSucesores(nodo)
        del base
    
    def modificarDependencia(self, codigo_dep = None, nombre_nuevo = None, codres_nuevo = None):
        """Permite modificar los atributos de la dependencia sin
                    modificar su ubicación en el organigrama."""
        def compararCodigo(nodo : NodoArbol, codigo):
            return nodo.data.codigo == codigo

        nodoDep : NodoArbol = self.raiz.buscar_nodo(codigo_dep, compararCodigo)
                
        if nombre_nuevo != None: 
            nodoDep.data.nombre = nombre_nuevo
        if codres_nuevo in self.personasPorCodigo.keys():

            #Caso donde la persona pertenece a otra dependencia y es jefe de ella
            self.raiz.recorrerOrganigrama(codres_nuevo, self.raiz.quitarJefe)
            self.personasPorCodigo[codres_nuevo].dependencia = nodoDep.data.codigo
            nodoDep.data.codigoResponsable = codres_nuevo
        else:
            raise ValueError("""No se puede asignar la persona como responsable
                              de la dependencia ya que no existe!""")

    def editarUbicacionDependencia(self, nodoMover: NodoArbol, nuevoNodoPadre: NodoArbol):
        """Agrega en los hijos de nodoDestino el objeto nodoMover y elimina de los hijos del anterior padre."""
        padre : NodoArbol = nodoMover.padre(self.raiz) #Buscamos el padre del nodo que se va mover
        padre.eliminar_hijo(nodoMover)
        nuevoNodoPadre.agregar_hijo(nodoMover)

    def ingresarPersona(self, nom, ape, ci, tel, dir, salario):
        cod = self.generarCodigoPersona()
        persona = Persona(codigo = cod, 
                          nombre = nom, 
                          apellido = ape, 
                          documento = ci, 
                          telefono = tel, 
                          direccion = dir, 
                          salario = salario)
        self.personasPorCodigo[cod] = persona
        
        
    def eliminarPersona(self, codigo_persona):
        self.raiz.recorrerOrganigrama(codigo_persona, NodoArbol.quitarJefe)
        self.personasPorCodigo.pop(codigo_persona)
        
    def modificarPersona(self, persona_nueva : Persona):
        # TODO: cambiar para poder utilizar parametros opcionales?
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
        
    def desasignarPersonasDeDependencia(self, codigo_dependencia):
        for persona in self.personasPorCodigo.values():
            if persona.dependencia == codigo_dependencia:
                persona.dependencia = None        

