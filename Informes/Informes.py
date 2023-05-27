from fpdf import FPDF
import warnings

warnings.simplefilter('default', DeprecationWarning)

pdf = FPDF()
pdf.add_font('Calibri', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibri.ttf')
pdf.add_font('CalibriBold', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibrib.ttf')
pdf.add_font('CalibriItalic', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibrii.ttf')

# TODO: Implementar
class Informes:
    def __init__(self) -> None:
        pass
    
    # TODO: Implementar
    def personalPorDependencia():
        nomdep = (input("Inserte nombre de la dependencia: "))


        #crear dpf
        pdf.add_page()
        pdf.set_font('CalibriBold', '', size=30)
        pdf.cell(0, 20, f'Dependencia: {nomdep}')
        nombre = ['Martin', 'Hiroto', 'Javier', 'Ivan', 'Fabrizio']
        apellido = ['Ferrer', 'Yamashita', 'Goto', 'Figueredo', 'Kawabata']
        
        pdf.write(txt="\n\n")
        pdf.set_font('Calibri', 'U' ,size=28)
        pdf.write(txt="Nombre y Apellido")
        pdf.set_font('Calibri', '', size=28)
        pdf.write(txt=':\n')
        pdf.set_font('CalibriItalic', '', size = 20)
        for i in range(5):
            pdf.cell(0,20, f'{nombre[i]} {apellido[i]}')
            pdf.set_font('CalibriItalic', '', size = 15)
            pdf.write(txt=" \n\n")
            pdf.set_font('CalibriItalic', '', size = 20)
        pdf.output("Personal por Dependencia.pdf")
        
    # TODO: Implementar
    def personalPorDependenciaExtendido():
        pass
    
    # TODO: Implementar
    def salarioPorDependencia():
        pass
    
    # TODO: Implementar
    def salarioPorDependenciaExtendido():
        pass
        
    # TODO: Implementar
    def imprimirOrganigrama():
        pass



    personalPorDependencia()