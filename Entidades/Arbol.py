from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Dependencia import Dependencia

class NodoArbol:
    """Clase que representa a un arbol de dependencias"""

    def __init__(self, data: 'Dependencia'):
        self.data = data
        self.children = []

    def agregar_hijo(self, nodo_hijo: 'NodoArbol'):
        if not isinstance(nodo_hijo, NodoArbol):
            raise ValueError("El hijo debe ser un objeto de tipo NodoArbol")
        self.children.append(nodo_hijo)

    def eliminar_hijo(self, nodo_hijo: 'NodoArbol'):
        self.children.remove(nodo_hijo)

    def __str__(self):
        return str(self.data)

