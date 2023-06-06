from dataclasses import dataclass
import param
from Entidades.BaseRegex import BaseRegex

class DependenciaRegex(BaseRegex):
    patrones = {
        "codigo": (r"^\d{3}$", "El código debe consistir en 3 dígitos"),
        "codigoResponsable": (r"^\d{4}$", "El código del responsable debe consistir en 4 dígitos"),
        "nombre": (r"^.{0,25}$", "El nombre debe tener hasta 25 caracteres"),
    }
    
@dataclass
class Dependencia(param.Parameterized):
    """Clase que representa una dependencia en nuestro organigrama"""

    codigo: str = param.String(None, regex=r"^\d{3}$")
    """Código interno único de 3 dígitos que representa a la dependencia"""

    codigoResponsable: str = param.String(None, regex=r"^\d{4}$")
    """Código de 4 dígitos del responsable de la dependencia"""

    nombre: str = param.String(None, regex=r"^.{0,25}$")
    """Nombre de la dependencia (hasta 25 caracteres)"""

    # Accessible representation for the user
    def __str__(self):
        return f"{self.nombre}"
    


        