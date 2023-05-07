from dataclasses import *
import param

@dataclass
class Persona(param.Parameterized):
    """Clase que representa a una persona en nuestro organigrama"""
    
    codigo: str = param.String(None, regex="^\d{4}$")
    """Codigo interno unico de 4 digitos que representa a la persona"""  
                            
    dependencia: str = param.String(None, regex="^\d{3}$")
    """Codigo de 3 digitos de la dependencia a la que la persona esta vinculada"""
    
    documento: str = param.String(None, regex="^.{0,15}$")                                   
    """Documento de identidad unica de la persona (hasta 15 letras)"""
    
    nombre: str = param.String(None, regex="^[A-Za-z]{0,15}$")                                      
    """Nombre de la persona (hasta 15 letras)"""
    
    apellido: str = param.String(None, regex="^[A-Za-z]{0,15}$")                                    
    """Apellido de la persona (hasta 15 letras)"""
    
    telefono: str = param.String(None, regex="^\d{0,12}$")                                    
    """Telefono de la persona (12 digitos)"""
    
    direccion: str = param.String(None, regex="^.{0,30}$")   
    """Dirección de la persona (Hasta 30 caracteres)"""
    
    salario : int = param.Integer(0, bounds=(0,999999999))  
    """Salario de la persona (Entero hasta 9 digitos)"""

    # Representacion accessible para el usuario (#TODO: posiblemente remover si vamos a tener todo
    # en interfaz grafica)
    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido} (C.I: {self.documento})"