from fpdf import FPDF
import warnings
from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Persona import *
from Archivo import *

warnings.simplefilter('default', DeprecationWarning)

# TODO: Implementar
class Informes:
    def __init__(self, archivo: Archivo) -> None:
        self.archivo = archivo
         
    def personalPorDependencia(self, dependencia : Dependencia):
        """
        Para una dependencia, presenta una lista de personas de la misma, 
        ordenada alfabéticamente por apellido y nombre. No incluye a las dependencias sucesoras.
        """

        # Crear PDF
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
        pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
        pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')
        pdf.add_page()

        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.write(txt=f'Dependencia: {dependencia.nombre}')
       
        # Imprimir Jefe
        pdf.write(txt='\n')
        pdf.set_font('Calibri', 'U', size=24)
        pdf.write(txt=f"Jefe:")
        jefe = self.archivo.personasPorCodigo.get(dependencia.codigoResponsable)
        pdf.set_font('Calibri', '', size=24)
        if jefe is None:
            pdf.write(txt=" No Asignado")
        else:
            pdf.write(txt=f" {jefe}")
            
        # Imprimir Titulo "Nombre y Apellido"
        pdf.set_font('Calibri', 'U' ,size=28)
        pdf.write(txt="\n\nNombres Completos del Personal:\n\n")

        # Imprimir Nombres y Apellidos
        pdf.set_font('CalibriItalic', '', size = 20)
        nombres = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == dependencia.codigo:
                nombres.append(f"• {persona.apellido}, {persona.nombre}") 
        nombres.sort()
        for nombre in nombres:
            pdf.write(txt=f'{nombre}')
            pdf.set_font('CalibriItalic', '', size = 15)
            pdf.write(txt=" \n\n")
            pdf.set_font('CalibriItalic', '', size = 20)

        # Guardar el archivo
        pdf.output("Personal_Por_Dependencia.pdf")
  
    def personalPorDependenciaExtendido(self, nodo: NodoArbol, pdf: FPDF = None, padre: NodoArbol = None):
        # Crear el pdf en la primera llamada
        if pdf is None:
            pdf = FPDF('P', 'mm', 'A4')
            pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
            pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
            pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')
        
        # Imprimir Datos de cada Dependencia:
        pdf.add_page()
        
        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.write(txt=f'Dependencia: {nodo.data.nombre}')
        
        # Imprimir padre si existe
        if padre is not None:
            pdf.write(txt='\n')
            pdf.set_font('Calibri', '', size=24)
            pdf.write(txt=f'(Subordinado a {padre.data.nombre})')
            
        # Imprimir Jefe
        pdf.write(txt='\n')
        pdf.set_font('Calibri', 'U', size=24)
        pdf.write(txt=f"Jefe:")
        jefe = self.archivo.personasPorCodigo.get(nodo.data.codigoResponsable)
        pdf.set_font('Calibri', '', size=24)
        if jefe is None:
            pdf.write(txt=" No Asignado")
        else:
            pdf.write(txt=f" {jefe}")
            
        # Imprimir Titulo "Nombre y Apellido"
        pdf.set_font('Calibri', 'U', size=28)
        pdf.write(txt="\n\nNombres Completos del Personal:\n\n")
        
        # Imprimir Nombres y Apellidos
        pdf.set_font('CalibriItalic', '', size=20)
        nombres = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == nodo.data.codigo:
                nombres.append(f"• {persona.apellido}, {persona.nombre}")
        nombres.sort()
        for nombre in nombres:
            pdf.write(txt=f'{nombre}')
            pdf.set_font('CalibriItalic', '', size=15)
            pdf.write(txt=" \n\n")
            pdf.set_font('CalibriItalic', '', size=20)

        # Transversar todos los nodos hijos recursivamente
        for child in nodo.children:
            self.personalPorDependenciaExtendido(child, pdf, nodo)

        # Si esta es la llamada incial, escribir el pdf con pdf.output()
        if padre is None:
            pdf.output("Personal_Por_Dependencia_Extendido.pdf")

    def salarioPorDependencia(self, dependencia: Dependencia):
        # Crear PDF
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
        pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
        pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')
        pdf.add_page()

        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.write(txt=f'Dependencia: {dependencia.nombre}')
    
        # Imprimir Cantidad de empleados y Suma de salarios
        pdf.write(txt="\n\n")
        pdf.set_font('CalibriItalic', '', size = 20)
        salarios = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == dependencia.codigo:
                salarios.append(persona.salario)
        pdf.write(txt=f'• Cantidad de personas: {len(salarios)}')
        pdf.write(txt="\n\n")
        pdf.write(txt=f'• Sueldo de la dependencia: {sum(salarios)}')

        # Guardar el archivo
        pdf.output("Salario_Por_Dependencia.pdf")
    
    # TODO: Implementar
    def salarioPorDependenciaExtendido(self, nodo: NodoArbol, pdf: FPDF = None, padre: NodoArbol = None):
        # Crear el pdf en la primera llamada
        if pdf is None:
            pdf = FPDF('P', 'mm', 'A4')
            pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
            pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
            pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')
        
        # Imprimir Datos de cada Dependencia:
        pdf.add_page()
        
        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.write(txt=f'Dependencia: {nodo.data.nombre}')
        # Imprimir padre si existe
        if padre is not None:
            pdf.write(txt='\n')
            pdf.set_font('Calibri', '', size=24)
            pdf.write(txt=f'(Subordinado a {padre.data.nombre})')
            
        # Imprimir Cantidad de empleados y Suma de salarios
        pdf.write(txt="\n\n")
        pdf.set_font('CalibriItalic', '', size = 20)
        salarios = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == nodo.data.codigo:
                salarios.append(persona.salario)
        pdf.write(txt=f'• Cantidad de personas: {len(salarios)}')
        pdf.write(txt="\n\n")
        pdf.write(txt=f'• Sueldo de la dependencia: {sum(salarios)}')

        # Transversar todos los nodos hijos recursivamente
        for child in nodo.children:
            self.salarioPorDependenciaExtendido(child, pdf, nodo)

        # Si esta es la llamada incial, escribir el pdf con pdf.output()
        if padre is None:
            pdf.output("Salario_Por_Dependencia_Extendido.pdf")
        
    # TODO: Implementar
    def imprimirOrganigrama(self):
        #imprimir el grafico del organigrama completo
        pass