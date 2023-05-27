from fpdf import FPDF
import warnings
from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Persona import *
from Archivo import *

warnings.simplefilter('default', DeprecationWarning)

pdf = FPDF('P', 'mm', 'A4')
pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')

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
        pdf.add_page()

        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.cell(0, 20, f'Dependencia: {dependencia.nombre}')

        # Imprimir Titulo "Nombre y Apellido"
        pdf.write(txt="\n\n")
        pdf.set_font('Calibri', 'U' ,size=28)
        pdf.write(txt="Nombre y Apellido")
        pdf.set_font('Calibri', '', size=28)
        pdf.write(txt=':\n')

        # Imprimir Nombres y Apellidos
        pdf.set_font('CalibriItalic', '', size = 20)
        nombres = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == dependencia.codigo:
                 nombres.append(f"{persona.apellido} {persona.nombre}")       
        nombres.sort()
        for nombre in nombres:
            pdf.cell(0,20, nombre)
            pdf.set_font('CalibriItalic', '', size = 15)
            pdf.write(txt=" \n\n")
            pdf.set_font('CalibriItalic', '', size = 20)

        # Guardar el archivo
        pdf.output("Personal por Dependencia.pdf")
        
    # TODO: Implementar
    def personalPorDependenciaExtendido(self, nodo: NodoArbol):
        # Hacer PDF de personas de la dependencia y sus hijos
        pass
    
    # TODO: Implementar
    def salarioPorDependencia(self, dependencia: Dependencia):
        # Crear PDF
        pdf.add_page()

        # Imprimir nombre de dependencia
        pdf.set_font('CalibriBold', '', size=30)
        pdf.cell(0, 20, f'Dependencia: {dependencia.nombre}')

        # Imprimir Cantidad de empleados y Suma de salarios
        pdf.set_font('CalibriItalic', '', size = 20)
        salarios = []
        for persona in self.archivo.personasPorCodigo.values():
            if persona.dependencia == dependencia.codigo:
                 salarios.append(f"{persona.salario}")       
        cantempdep = len(salarios)
        sumsueldep = sum(salarios)
        pdf.cell(0,20, f'Cantidad de personas: {cantempdep}')
        pdf.cell(0,20, f'Sueldo de la dependencia: {sumsueldep}')

        # Guardar el archivo
        pdf.output("SalarioPorDependencia.pdf")
    
    # TODO: Implementar
    def salarioPorDependenciaExtendido(self, nodo: NodoArbol):
        # Hacer PDF de sueldo de la dependencia y sus hijos
        pass
        
    # TODO: Implementar
    def imprimirOrganigrama():
        #imprimir el grafico del organigrama completo
        pass