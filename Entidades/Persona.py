from dataclasses import *
import param
from Entidades.BaseRegex import BaseRegex

@dataclass
class Persona(param.Parameterized):
    """Clase que representa a una persona en nuestro organigrama"""
    
    codigo: str = param.String(None, regex=r"^\d{4}$")
    """Codigo interno único de 4 dígitos que representa a la persona"""  
                            
    dependencia: str = param.String(None, regex=r"^\d{3}$")
    """Código de 3 dígitos de la dependencia a la que la persona está vinculada"""
    
    documento: str = param.String(None, regex=r"^.{0,15}$")                                   
    """Documento de identidad única de la persona (hasta 15 letras)"""
    
    nombre: str = param.String(None, regex=r"^[A-Za-zÀ-ÿ_ ]{0,15}$")                                      
    """Nombre de la persona (hasta 15 letras)"""
    
    apellido: str = param.String(None, regex=r"^[A-Za-zÀ-ÿ_ ]{0,15}$")                                    
    """Apellido de la persona (hasta 15 letras)"""
    
    telefono: str = param.String(None, regex=r"^\d{0,12}$")                                    
    """Teléfono de la persona (12 dígitos)"""
    
    direccion: str = param.String(None, regex=r"^.{0,30}$")   
    """Dirección de la persona (hasta 30 caracteres)"""
    
    salario: int = param.Integer(0, bounds=(0, 999999999))  
    """Salario de la persona (entero hasta 9 dígitos)"""


    # Representación accesible para el usuario
    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido} (C.I: {self.documento})"
    
class PersonaRegex(BaseRegex):
    patrones = {
        "codigo": (r"^\d{4}$", "El código debe consistir en 4 dígitos"),
        "dependencia": (r"^\d{3}$", "El código de la dependencia debe consistir en 3 dígitos"),
        "documento": (r"^.{0,15}$", "El documento puede tener hasta 15 caracteres"),
        "nombre": (r"^[A-Za-zÀ-ÿ_ ]{0,15}$", "El nombre puede tener hasta 15 letras"),
        "apellido": (r"^[A-Za-zÀ-ÿ_ ]{0,15}$", "El apellido puede tener hasta 15 letras"),
        "telefono": (r"^\d{0,12}$", "El teléfono puede consistir en hasta 12 dígitos"),
        "direccion": (r"^.{0,30}$", "La dirección puede tener hasta 30 caracteres"),
        "salario": (r"^\d{0,9}$", "El salario puede consistir en hasta 9 dígitos"),
    }