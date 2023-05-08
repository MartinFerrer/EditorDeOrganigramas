from dataclasses import dataclass
import param
from random import randint
from typing import List

@dataclass
class Dependencia(param.Parameterized):
    """Clase que representa una dependencia en nuestro organigrama"""

    codigo: str = param.String(None, regex="^\d{3}$")
    """Código interno único de 3 dígitos que representa a la dependencia"""

    codigoResponsable: str = param.String(None, regex="^\d{4}$")
    """Código de 4 dígitos del responsable de la dependencia"""

    nombre: str = param.String(None, regex="^.{0,20}$")
    """Nombre de la dependencia (hasta 20 caracteres)"""

    def __post_init__(self):
        self.codigo = Dependencia.genera_code(self)
    # Representacion accessible para el usuario (#TODO: posiblemente remover si vamos a tener todo
    # en interfaz grafica)
    def __str__(self):
        return f"Dependencia: {self.nombre}, Código: {self.codigo}, Responsable: {self.codigoResponsable}"
    
    # TODO: Generar codigo unico entre 0 y 999
    def genera_code(self):
        code = randint(0, 100)
        if code < 10:
            code = "00" + str(code)
        elif code >= 10 and code < 100:
            code = "0" + str(code)
        else:
            code = str(code)

        # if code not in lista de codigos:
        #     lista de codigos.append(code)
        return code

Persona1 = Dependencia()
print(Persona1.codigo)
        