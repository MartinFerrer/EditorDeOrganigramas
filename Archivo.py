from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *

def marcar_archivo_modificado(func):
    """Decorador para asignar que una funcion modifica el archivo y este requiere guardarse para no perder cambios"""
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, Archivo):
                arg.modificado = True
        for arg in kwargs.values():
            if isinstance(arg, Archivo):
                arg.modificado = True
        return func(*args, **kwargs)
    return wrapper

class Archivo():

    def __init__(self) -> None:
        self.ruta: str = ""
        """Ruta donde se guarda el archivo""" 
        
        self.modificado: bool = False
        """Bandera que determina si el archivo tiene cambios sin guardar"""
        
        self.organigrama: Organigrama = Organigrama()
        """Informacion acerca del organigrama"""

        self.raiz: NodoArbol = None
        """Raiz del arbol con dependencias que representan al organigrama"""

        self.codigosDeDependencias: list[str] = []
        """Una lista que contiene todos los codigos de dependencias utilizados"""

        self.personasPorCodigo: dict[str, Persona] = {}
        """Un diccionario relacionando a los objetos de personas con su codigo de 4 digitos"""
  
    # Sobreescribir para asignar que se modifico el archivo si alguna de las propiedades es asignada
    def __setattr__(self, name, value):
        if name != "modificado" and name != "ruta":
            self.modificado = True
        super().__setattr__(name, value)

    def generarCodigoDependencia(self):
        """Genera codigo de dependencia y verifica que no exista.""" 
        for i in range(1000):
            codigo = str(i).zfill(3)
            if codigo not in self.codigosDeDependencias:
                return codigo
        raise RuntimeError("No se pudo generar codigo para dependencia! No hay codigos disponibles.")
    
    def generarCodigoPersona(self):
        """Genera codigo de persona y verifica que no exista.""" 
        for i in range(10000):
            codigo = str(i).zfill(4)
            if codigo not in self.personasPorCodigo.keys():
                return codigo
        raise RuntimeError("No se pudo generar codigo para persona! No hay codigos disponibles.")

    @marcar_archivo_modificado
    def crearDependencia(self, nombre, nodoPadre : NodoArbol): 
        """
        Crea una dependencia generando automaticamente su codigo y utilizando el nombre dado
        La dependencia es insertada como hijo del padre, 
        si el archivo no tiene raiz se asigna indiferentemente a esta
        """
        codigo = self.generarCodigoDependencia()
        dependencia = Dependencia(codigo = codigo, codigoResponsable = None, nombre = nombre)
        nodo = NodoArbol(dependencia)

        # Caso que la dependencia nueva sea la unica dependencia organigrama (su raiz)
        if self.raiz is None:
            self.raiz = nodo
        else:
            nodoPadre.agregarHijo(nodo)
        self.codigosDeDependencias.append(codigo)
    
    @marcar_archivo_modificado
    def eliminarDependencia(self, nodo: NodoArbol):
        """Permite eliminar una dependencia existente y todas las dependencias sucesoras de la misma.""" 
        padre : NodoArbol = nodo.padre(self.raiz)
        # Si el nodo no tiene padre significa que es la raiz del archivo
        if padre is None:
            self.raiz = None
        else:
            padre.eliminarHijo(nodo)
        self.eliminarNodoYSucesores(nodo)

    @marcar_archivo_modificado
    def eliminarNodoYSucesores(self, base: 'NodoArbol'): 
        """Elimina los sucesores de la dependencia "base" y desasigna a sus trabajadores """
        self.desasignarPersonasDeDependencia(base.dep.codigo)
        self.codigosDeDependencias.remove(base.dep.codigo)
        
        # Crear una copia de la lista de hijos para no editar la lista que iteramos para la recursion
        nodos_a_remover = [nodo for nodo in base.hijos]

        for nodo in nodos_a_remover:
            base.hijos.remove(nodo)
            self.eliminarNodoYSucesores(nodo)
    
    
    @marcar_archivo_modificado 
    def modificarDependencia(self, codigoDependencia = None, nombreNuevo = None, codresNuevo = None):
        """Permite cambiar el nombre de la dependencia y su persona responsable (jefe)"""
                    
        nodoDep : NodoArbol = self.raiz.buscarNodo(codigoDependencia, NodoArbol.compararCodigo)
        
        if nombreNuevo is not None: 
            nodoDep.dep.nombre = nombreNuevo
            
        if codresNuevo is not None:
            if codresNuevo in self.personasPorCodigo.keys():
                #Caso donde la persona pertenece a otra dependencia y es jefe de ella
                self.raiz.recorrerArbol(NodoArbol.quitarJefe, codresNuevo)
                # Asignar jefe de dependencia
                self.personasPorCodigo[codresNuevo].dependencia = nodoDep.dep.codigo
                nodoDep.dep.codigoResponsable = codresNuevo
            else:
                raise ValueError("""No se puede asignar la persona como responsable
                                de la dependencia ya que no existe!""")

    @marcar_archivo_modificado  
    def editarUbicacionDependencia(self, nodoMover: NodoArbol, nuevoNodoPadre: NodoArbol):
        """Agrega en los hijos de nodoDestino el objeto nodoMover y elimina de los hijos del anterior padre."""
        #Buscamos el padre del nodo que se va mover
        padre : NodoArbol = nodoMover.padre(self.raiz) 
        padre.eliminarHijo(nodoMover)
        nuevoNodoPadre.agregarHijo(nodoMover)

    @marcar_archivo_modificado
    def ingresarPersona(self, persona: Persona):
        """Genera el codigo para el objeto persona y lo ingresa en el diccionario personasPorCodigo"""
        persona.codigo = self.generarCodigoPersona()
        self.personasPorCodigo[persona.codigo] = persona
        
    @marcar_archivo_modificado   
    def eliminarPersona(self, persona: Persona):
        """Elimina la persona de la lista de personas y ademas la elimina como jefe si lo es de alguna dependencia"""
        self.raiz.recorrerArbol(NodoArbol.quitarJefe, persona.codigo)
        self.personasPorCodigo.pop(persona.codigo)
    
    @marcar_archivo_modificado
    def modificarPersona(self, codigoPersonaModificada, datosNuevos: Persona):
        """Modifica la persona dada por su codigo copiando los datos nuevos dados como objeto Persona"""
        persona_destino = self.personasPorCodigo[codigoPersonaModificada]
        persona_destino.nombre = datosNuevos.nombre
        persona_destino.apellido = datosNuevos.apellido
        persona_destino.telefono = datosNuevos.telefono
        persona_destino.direccion = datosNuevos.direccion
        persona_destino.salario = datosNuevos.salario
    
    @marcar_archivo_modificado  
    def asignarPersonaADependencia(self, codigoPersona, codigoDependencia):
        """Asigna la persona como perteneciente a una dependencia (Nota: no la hace jefe)"""
        #Caso donde la persona pertenece a otra dependencia y es jefe de ella
        self.raiz.recorrerArbol(NodoArbol.quitarJefe, codigoPersona)
        # Asignar persona a la dependencia
        persona = self.personasPorCodigo[codigoPersona]
        persona.dependencia = codigoDependencia
            

    @marcar_archivo_modificado   
    def desasignarPersonasDeDependencia(self, codigoDependencia):
        """Desasigna todas las personas de dependencia"""
        for persona in self.personasPorCodigo.values():
            if persona.dependencia == codigoDependencia:
                persona.dependencia = None        

