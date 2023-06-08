class BaseRegex:
    """
    Clase auxiliar para definir un diccionario con los atributos de la clase como clave y 
    patrones RegEx (Expresiones regulares) como valores en una Tupla (patron, descripcion)
    """
    
    patrones = {}
    """Patrones en un diccionario con valores como Tupla (patron, descripcion)"""
    
    @staticmethod
    def regex(clave):
        return BaseRegex.patrones[clave][0]
    
    @staticmethod
    def descripcion(clave):
        return BaseRegex.patrones[clave][1]