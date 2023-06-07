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
        """Buscar recursivamente un nodo que cumpla que la funcion de buscador retorne verdadero"""
        if buscador(self, buscado):
            return self
        for nodo in self.children:
            resultado = nodo.buscar_nodo(buscado, buscador)
            if resultado is not None:  
                return resultado
        return None 
    
    def recorrer_arbol(self, function: Callable[['NodoArbol', Any], None], *args: Any, **kwargs: Any) -> None:
        """Recorrer el arbol llamando una funcion que retorna nada que opera sobre cada nodo recursivamente
        La funcion puede contener cualquier cantidad de argumentos adicionales"""
        function(self, *args, **kwargs)
        for nodo in self.children:
            nodo.recorrer_arbol(function, *args, **kwargs)

    def nodo_es_hijo(self, nodo) -> bool:
        return nodo in self.children

    def padre(self, raiz: 'NodoArbol') -> 'NodoArbol':
        return raiz.buscar_nodo(self, NodoArbol.nodo_es_hijo)
    
    def compararCodigo(self, codigoDep):
        return self.data.codigo == codigoDep
    
    def compararCodigoResponsable(self, codigoPersona):
        return self.data.codigoResponsable == codigoPersona
    
    def quitarJefe(self, codigoPersona) -> 'None':
        """Esta funcion nos sirve para cuando tenemos que quitarle a una
            persona del cargo de jefe de alguna dependencia"""
        if self.data.codigoResponsable == codigoPersona:
            self.data.codigoResponsable = None

    # Representacion para debug
    def __repr__(self) -> str:
        return f"(Dependencia: {self.data}, Hijos: {self.children})"
