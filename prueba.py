class Prueba:
    dic = {}
    def __init__(self, nombre, edad, codigo) -> None:
        self.nombre = nombre
        self.edad = edad
        self.codigo = self.guarda_code(codigo)


    
    def guarda_code(self, code):
        Prueba.dic[code] = self
        return code


Persona1 = Prueba("Juan", 23, "1110")
print(Persona1.nombre)
print(Persona1.edad)
print(Persona1.codigo)
Persona2 = Prueba.dic["1110"]
Persona2.nombre = "Ramon"
print("\n\n")
print(Persona2.nombre)
print(Persona1.nombre)

