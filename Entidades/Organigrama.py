from dataclasses import dataclass
import param
from datetime import datetime

@dataclass
class Organigrama(param.Parameterized):
    """Clase que representa un organigrama"""
    
    codigo: str = param.String(None, regex="^\d{5}$")
    """Código interno único de 5 dígitos que representa al organigrama"""
    
    organizacion: str = param.String(None, regex="^.{0,20}$")
    """Nombre de la organización (hasta 20 caracteres)"""
    
    fecha: datetime = param.Date(None)
    """Fecha del organigrama"""
    
    # Representacion accessible para el usuario (#TODO: posiblemente remover si vamos a tener todo
    # en interfaz grafica)
    def __str__(self):
        return f"Organigrama: {self.organizacion}, Código: {self.codigo}, Fecha: {self.fecha}"