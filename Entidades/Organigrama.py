import param
from dataclasses import dataclass
from datetime import datetime
from Entidades.BaseRegex import BaseRegex

@dataclass
class Organigrama(param.Parameterized):
    """Clase que representa un organigrama"""
    
    codigo: str = param.String(None, regex="^\d{5}$")
    """Código interno único de 5 dígitos que representa al organigrama"""
    
    organizacion: str = param.String(None, regex=r"^.{0,20}$")
    """Nombre de la organización (hasta 20 caracteres)"""
    
    fecha: datetime = param.Date(None)
    """Fecha del organigrama"""
    
    # Representación accesible para el usuario
    def __str__(self):
        return f"Organigrama: {self.organizacion}, Código: {self.codigo}, Fecha: {self.fecha}"
    
class OrganigramaRegex(BaseRegex):
    """Patrones RegEx y descripciones de los atributos de Organigrama"""
    patrones = {
        "codigo": (r"^\d{5}$", "El código debe consistir en 5 dígitos"),
        "organizacion": (r"^.{0,20}$", "La organización debe tener hasta 20 caracteres"),
    }