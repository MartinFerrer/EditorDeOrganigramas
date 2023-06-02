import copy 
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
Persona2 = Persona1
print(Persona1.nombre)

print(Persona2.nombre)
print(Persona2.edad)
Persona2.nombre = "Jose"
print(Persona1.nombre)

# print(Persona2)
# Persona2 = copy.deepcopy(Persona1)
# print(Persona2)

# print(Persona1.nombre)

# print(Persona2.nombre)

# print(Persona2.edad)

# print(Persona2.codigo)
print(Prueba.dic)
Persona2.busqueda("1010")
print(Persona1.dic.keys())
print(Persona1.dic.values())
Prueba.dic = {}
print(Prueba.dic)



