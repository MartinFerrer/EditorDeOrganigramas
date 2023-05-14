from fpdf import FPDF
import warnings

warnings.simplefilter('default', DeprecationWarning)

pdf = FPDF()
pdf.add_font('Calibrinormal', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibri.ttf')
pdf.add_font('Calibrilight', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibril.ttf')
pdf.add_font('Calibricursiva', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibrii.ttf')
pdf.add_font('Calibricursivalight', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibrili.ttf')
pdf.add_font('Calibricursivanegrita', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibriz.ttf')
pdf.add_font('Calibrinegrita', '', r'C:\Users\hiros\OneDrive\Documentos\GitHub\EditorDeOrganigramas\Informes\fuentes\calibrib.ttf')


# TODO: Implementar
class Informes:
    def __init__(self) -> None:
        pass
    
    # TODO: Implementar
    def personalPorDependencia():
        nomdep = (input("Inserte nombre de la dependencia: "))


        #crear dpf
        pdf.add_page()
        pdf.set_font('Calibrinegrita', size=30)
        pdf.cell(0, 20, f'Dependencia: {nomdep}')
        nombre = ['Martin', 'Hiroto', 'Javier', 'Ivan', 'Fabrizio']
        apellido = ['Ferrer', 'Yamashita', 'Goto', 'Figueredo', 'Kawabata']
        
        pdf.write(txt="\n\n")
        pdf.set_font('Calibricursiva', size=28)
        pdf.write(txt="Nombre y Apellido:\n")
        pdf.set_font('Calibrinormal', size = 20)
        for i in range(5):
            pdf.cell(0,20, f'{nombre[i]} {apellido[i]}')
            pdf.write(txt="\n\n")
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