from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from Dependencia import Dependencia

class NodoArbol:
    """Clase que representa a un arbol de dependencias"""

    def __init__(self, data: 'Dependencia'):
        self.data = data
        self.children : list[NodoArbol] = []

    def __str__(self):
        return str(self.data)

    def agregar_hijo(self, nodo_hijo: 'NodoArbol'):
        if not isinstance(nodo_hijo, NodoArbol):
            raise ValueError("El hijo debe ser un objeto de tipo NodoArbol")
        self.children.append(nodo_hijo)

    def eliminar_hijo(self, nodo_hijo: 'NodoArbol'):
        self.children.remove(nodo_hijo)

    def buscar_nodo(self, buscado, buscador: Callable[['NodoArbol', Any], bool]) -> 'NodoArbol':
        if buscador(self, buscado):
            return self
        for nodo in self.children:
            resultado = nodo.buscar_nodo(buscado, buscador)
            if resultado is not None:  
                return resultado
        return None 
    
    def nodo_es_hijo(self, nodo) -> bool:
        return nodo in self.children

    def padre(self, raiz: 'NodoArbol') -> 'NodoArbol':
        return raiz.buscar_nodo(self, NodoArbol.nodo_es_hijo)