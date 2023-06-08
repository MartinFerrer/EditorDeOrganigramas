from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from Dependencia import Dependencia

class NodoArbol:
    """Clase que representa a un arbol de dependencias"""

    def __init__(self, dependencia: 'Dependencia'):
        self.dep = dependencia
        """Dependencia correspondiente al nodo"""
        self.hijos : list[NodoArbol] = []
        """Los hijos del nodo (Máximo 5)"""

    # Representación para el usuario, mostrar nombre de dependencia
    def __str__(self):
        return str(self.dep)

    # Representación para debug
    def __repr__(self) -> str:
        return f"(Dependencia: {self.dep}, Hijos: {self.hijos})"

    def agregarHijo(self, nodo_hijo: 'NodoArbol'):
        if not isinstance(nodo_hijo, NodoArbol):
            raise ValueError("El hijo debe ser un objeto de tipo NodoArbol")
        self.hijos.append(nodo_hijo)

    def eliminarHijo(self, nodo_hijo: 'NodoArbol'):
        self.hijos.remove(nodo_hijo)

    def buscarNodo(self, buscado, buscador: Callable[['NodoArbol', Any], bool]) -> 'NodoArbol':
        """Buscar recursivamente un nodo que cumpla que la funcion de buscador retorne verdadero"""
        if buscador(self, buscado): 
            return self             # Se encontro el nodo buscado en este nodo
        for nodo in self.hijos:
            resultado = nodo.buscarNodo(buscado, buscador)
            if resultado is not None:  
                return resultado    # Nodo encontrado
        return None                 # No se encontro el nodo buscado en este nodo
    
    def recorrerArbol(self, function: Callable[['NodoArbol', Any], None], *args: Any, **kwargs: Any) -> None:
        """Recorrer el arbol llamando una funcion que retorna nada que opera sobre cada nodo recursivamente
        La funcion puede contener cualquier cantidad de argumentos adicionales"""
        function(self, *args, **kwargs)
        for nodo in self.hijos:
            nodo.recorrerArbol(function, *args, **kwargs)

    def nodoEsHijo(self, nodo) -> bool:
        return nodo in self.hijos

    def padre(self, raiz: 'NodoArbol') -> 'NodoArbol':
        return raiz.buscarNodo(self, NodoArbol.nodoEsHijo)
    
    def compararCodigo(self, codigoDep):
        return self.dep.codigo == codigoDep
    
    def quitarJefe(self, codigoPersona) -> 'None':
        """Esta funcion nos sirve para cuando tenemos que quitarle a una
            persona del cargo de jefe de alguna dependencia"""
        if self.dep.codigoResponsable == codigoPersona:
            self.dep.codigoResponsable = None

    def quitarCodigoResponsable(self):
        """Asigna valor None al codigo responsable en la dependencia del nodo"""
        self.dep.codigoResponsable = None
