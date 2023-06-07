from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Organigrama import *
from Entidades.Persona import *

# Decorador para asignar que una funcion
def marcar_archivo_modificado(func):
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, Archivo):
                # TODO: remover print
                #print(f"marcando {arg} como modificado con decorador")
                arg.modificado = True
        for arg in kwargs.values():
            if isinstance(arg, Archivo):
                # TODO: remover print
                #print(f"marcando {arg} como modificado con decorador")
                arg.modificado = True
        return func(*args, **kwargs)
    return wrapper

class Archivo():

    def __init__(self) -> None:
        self.ruta : str = ""
        """Ruta donde se guarda el archivo""" 
        
        self.modificado : bool = False
        """Bandera que determina si el archivo tiene cambios sin guardar"""
        
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
        
    # Sobreescribir para asignar que se modifico el archivo si alguna de las propiedades es asignada
    def __setattr__(self, name, value):
        if name != "modificado" and name != "ruta":
            # TODO: remover print
            print(f"marcando {name} como modificado con __setattr__")
            self.modificado = True
        super().__setattr__(name, value)

    @marcar_archivo_modificado
    def generarCodigoDependencia(self): 
        """Genera codigo de dependencia y verifica que no exista.""" 
        if self.codigoDependenciaMasAlto != 999:
            codigo = self.codigoDependenciaMasAlto + 1
            self.codigoDependenciaMasAlto = codigo
            return str(codigo).zfill(3)
        else:
            for i in range(1000):
                codigo = str(i).zfill(3)
                if codigo not in self.dependenciasPorCodigo:
                    return codigo
            raise RuntimeError("No se pudo generar codigo para dependencia! No hay codigos disponibles.")
    
    @marcar_archivo_modificado
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
    
    @marcar_archivo_modificado
    def quitarCodres(self, raiz : NodoArbol):
        """Recorre todo el organigrama para poner en None el Codres"""
        raiz.data.codigoResponsable = None
        for nodo in raiz.children:
            self.quitarCodres(nodo)

    @marcar_archivo_modificado
    def crearDependencia(self, nom, nodoPadre : NodoArbol): 
        cod = self.generarCodigoDependencia()
        dep = Dependencia(codigo = cod, codigoResponsable = None, nombre = nom)
        nodo = NodoArbol(dep)

        #Caso que sea la primera dependencia agregada en el organigrama
        if nodoPadre.data == None:
            nodoPadre.data = dep
        else:
            nodoPadre.agregar_hijo(nodo)
            
        self.dependenciasPorCodigo.append(cod)
    
    @marcar_archivo_modificado
    def eliminarDependencia(self, codigoDependencia):
        """Permite eliminar una dependencia existente y todas las 
           dependencias sucesoras de la misma."""
        nodo = self.raiz.buscar_nodo(codigoDependencia, NodoArbol.compararCodigo) #Retorna el nodo que tiene el codigo indicado en el argumento

        padre : NodoArbol = nodo.padre(self.raiz)
        # Si el nodo no tiene padre significa que es la raiz del archivo
        if padre is None:
            self.raiz = None
        else:
            padre.eliminar_hijo(nodo)
        self.eliminarNodoYSucesores(nodo)

    @marcar_archivo_modificado
    def eliminarNodoYSucesores(self, base: 'NodoArbol'): 
        """Elimina los sucesores de la dependencia "base" y desasigna a sus trabajadores """
        self.desasignarPersonasDeDependencia(base.data.codigo)
        self.dependenciasPorCodigo.remove(base.data.codigo)
        
        # Crear una copia de la lista de hijos para no editar la lista que iteramos para la recursion
        nodos_a_remover = [nodo for nodo in base.children]

        for nodo in nodos_a_remover:
            base.children.remove(nodo)
            self.eliminarNodoYSucesores(nodo)
    
    @marcar_archivo_modificado 
    def modificarDependencia(self, codigoDependencia = None, nombre_nuevo = None, codresNuevo = None):
        """Permite modificar los atributos de la dependencia sin
                    modificar su ubicación en el organigrama."""


        nodoDep : NodoArbol = self.raiz.buscar_nodo(codigoDependencia, NodoArbol.compararCodigo)
                
        if nombre_nuevo is not None: 
            nodoDep.data.nombre = nombre_nuevo
            
        if codresNuevo is not None:
            if codresNuevo in self.personasPorCodigo.keys():
                #Caso donde la persona pertenece a otra dependencia y es jefe de ella
                self.raiz.recorrerOrganigrama(codresNuevo, NodoArbol.quitarJefe)
                self.personasPorCodigo[codresNuevo].dependencia = nodoDep.data.codigo
                nodoDep.data.codigoResponsable = codresNuevo
            else:
                raise ValueError("""No se puede asignar la persona como responsable
                                de la dependencia ya que no existe!""")

    @marcar_archivo_modificado  
    def editarUbicacionDependencia(self, nodoMover: NodoArbol, nuevoNodoPadre: NodoArbol):
        """Agrega en los hijos de nodoDestino el objeto nodoMover y elimina de los hijos del anterior padre."""
        padre : NodoArbol = nodoMover.padre(self.raiz) #Buscamos el padre del nodo que se va mover
        padre.eliminar_hijo(nodoMover)
        nuevoNodoPadre.agregar_hijo(nodoMover)

    @marcar_archivo_modificado
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
        
    @marcar_archivo_modificado   
    def eliminarPersona(self, codigo_persona):
        self.raiz.recorrerOrganigrama(codigo_persona, NodoArbol.quitarJefe)
        self.personasPorCodigo.pop(codigo_persona)
    
    @marcar_archivo_modificado    
    def modificarPersona(self, persona_nueva : Persona):
        # TODO: cambiar para poder utilizar parametros opcionales?
        persona_destino = self.personasPorCodigo[persona_nueva.codigo]
        persona_destino.dependencia = persona_nueva.dependencia
        persona_destino.nombre = persona_nueva.nombre
        persona_destino.apellido = persona_nueva.apellido
        persona_destino.telefono = persona_nueva.telefono
        persona_destino.direccion = persona_nueva.direccion
        persona_destino.salario = persona_nueva.salario
    
    @marcar_archivo_modificado  
    def asignarPersonaADependencia(self, cod_persona, codigoDependencia, esJefe):

        # def compararCodigo(nodo : NodoArbol, codigo):
        #     return nodo.data.codigo == codigo
        
        persona = self.personasPorCodigo[cod_persona]
        persona.dependencia = codigoDependencia
        if esJefe:
            nodo = self.raiz.buscar_nodo(codigoDependencia, NodoArbol.compararCodigo)
            nodo.data.codigoResponsable = cod_persona
    
    @marcar_archivo_modificado   
    def desasignarPersonasDeDependencia(self, codigo_dependencia):
        for persona in self.personasPorCodigo.values():
            if persona.dependencia == codigo_dependencia:
                persona.dependencia = None        

