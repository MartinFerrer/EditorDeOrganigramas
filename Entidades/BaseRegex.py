class BaseRegex:
    patrones = {}
    
    @staticmethod
    def regex(clave):
        print(BaseRegex.patrones)
        return BaseRegex.patrones[clave][0]
    
    @staticmethod
    def descripcion(clave):
        print(BaseRegex.patrones)
        return BaseRegex.patrones[clave][1]