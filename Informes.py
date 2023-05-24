from fpdf import FPDF
import warnings
from Entidades.Arbol import *
from Entidades.Dependencia import *
from Entidades.Persona import *

warnings.simplefilter('default', DeprecationWarning)

pdf = FPDF('P', 'mm', 'A4')
pdf.add_font('Calibri', '', r'.\fuentes\calibri.ttf')
pdf.add_font('CalibriBold', '', r'.\fuentes\calibrib.ttf')
pdf.add_font('CalibriItalic', '', r'.\fuentes\calibrii.ttf')

# TODO: Implementar
class Informes:
    def __init__(self) -> None:
        pass
    
    # TODO: Implementar
    def personalPorDependencia():
        # Hacer PDF de personas solo de una dependencia
        nomdep = input("Inserte nombre de la dependencia: ")
        if len(nomdep) > 25:
            print("El nombre de la dependencia no puede tener más de 25 caracteres, inserte de nuevo.")
            nomdep = input("Inserte nombre de la dependencia: ")
        
        


        #crear dpf
        pdf.add_page()
        pdf.set_font('CalibriBold', '', size=30)
        pdf.cell(0, 20, f'Dependencia: {nomdep}')
        nombre = ['Martin', 'Hiroto', 'Javier', 'Ivan', 'Fabrizio']
        apellido = ['Cano', 'Yamashita', 'Goto', 'Figueredo', 'Kawabata']
        
        pdf.write(txt="\n\n")
        pdf.set_font('Calibri', 'U' ,size=28)
        pdf.write(txt="Nombre y Apellido")
        pdf.set_font('Calibri', '', size=28)
        pdf.write(txt=':\n')
        pdf.set_font('CalibriItalic', '', size = 20)
        for i in range(len(nombre)):
            pdf.cell(0,20, f'{nombre[i]} {apellido[i]}')
            pdf.set_font('CalibriItalic', '', size = 15)
            pdf.write(txt=" \n\n")
            pdf.set_font('CalibriItalic', '', size = 20)
        pdf.output("Personal por Dependencia.pdf")
        
    # TODO: Implementar
    def personalPorDependenciaExtendido():
        # Hacer PDF de personas de la dependencia y sus hijos
        pass
    
    # TODO: Implementar
    def salarioPorDependencia():
        # Hacer PDF de sueldo solo de un dependencia
        pass
    
    # TODO: Implementar
    def salarioPorDependenciaExtendido():
        # Hacer PDF de sueldo de la dependencia y sus hijos
        pass
        
    # TODO: Implementar
    def imprimirOrganigrama():
        #imprimir el grafico del organigrama completo
        pass



    personalPorDependencia()