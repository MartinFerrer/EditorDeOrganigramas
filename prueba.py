class Prueba:
    dic = {}
    def __init__(self, nombre, edad, codigo) -> None:
        self.nombre = nombre
        self.edad = edad
        self.codigo = self.guarda_code(codigo)


    
    def guarda_code(self, code):
        Prueba.dic[code] = self
        return code
    
    def busqueda(self, code):
        for elem in Prueba.dic.keys():
            if Prueba.dic[elem].codigo == code:
                print(f"Su nombre es {Prueba.dic[elem].nombre}")


Persona1 = Prueba("Juan", 23, "1110")
Persona2 = Prueba("Fabri", 24, "1010")

Persona2.busqueda("1010")




