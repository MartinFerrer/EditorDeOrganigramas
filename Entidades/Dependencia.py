from dataclasses import dataclass
import param

@dataclass
class Dependencia(param.Parameterized):
    """Clase que representa una dependencia en nuestro organigrama"""

    codigo: str = param.String(None, regex="^\d{3}$")
    """Código interno único de 3 dígitos que representa a la dependencia"""

    codigoResponsable: str = param.String(None, regex="^\d{4}$")
    """Código de 4 dígitos del responsable de la dependencia"""

    nombre: str = param.String(None, regex="^.{0,20}$")
    """Nombre de la dependencia (hasta 20 caracteres)"""

    # Representacion accessible para el usuario (#TODO: posiblemente remover si vamos a tener todo
    # en interfaz grafica)
    def __str__(self):
        return f"Dependencia: {self.nombre}, Código: {self.codigo}, Responsable: {self.codigoResponsable}"
    
    


        