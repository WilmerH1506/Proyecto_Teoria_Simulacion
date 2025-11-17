# export_pdf.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import tempfile
import os

def exportar_simulacion_pdf(nombre_archivo, datos_variable, datos_tradicional, datos_pe, grafica_pe):
    """
    Genera un PDF con las 3 pestañas de simulación.
    
    Parámetros:
        nombre_archivo (str): ruta donde guardar el PDF final.
        datos_variable (dict): resultados del estado de costos variables.
        datos_tradicional (dict): resultados del estado tradicional.
        datos_pe (dict): resultados del cálculo de punto de equilibrio.
        grafica_pe (Figure): figura matplotlib ya generada.
    """

    styles = getSampleStyleSheet()
    elementos = []

    # =============================
    # 1. ESTADO DE COSTOS VARIABLES
    # =============================
    elementos.append(Paragraph("<b>ESTADO DE RESULTADOS - COSTO VARIABLE</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    tabla1_data = [["Concepto", "Valor", "%"]]

    for key, (valor, porcentaje) in datos_variable.items():
        tabla1_data.append([
            key,
            f"${valor:,.2f}",
            f"{porcentaje*100:,.2f} %"
        ])

    tabla1 = Table(tabla1_data, colWidths=[250, 120, 80])
    tabla1.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.gray),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ]))

    elementos.append(tabla1)
    elementos.append(Spacer(1, 20))

    # =============================
    # 2. ESTADO TRADICIONAL
    # =============================
    elementos.append(Paragraph("<b>ESTADO DE RESULTADOS - TRADICIONAL</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    tabla2_data = [["Concepto", "Valor", "%"]]

    for key, (valor, porcentaje) in datos_tradicional.items():
        tabla2_data.append([
            key,
            f"${valor:,.2f}",
            f"{porcentaje*100:,.2f} %"
        ])

    tabla2 = Table(tabla2_data, colWidths=[250, 120, 80])
    tabla2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.gray),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ]))

    elementos.append(tabla2)
    elementos.append(Spacer(1, 20))

    # =============================
    # 3. PUNTO DE EQUILIBRIO
    # =============================
    elementos.append(Paragraph("<b>PUNTO DE EQUILIBRIO</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    tabla3_data = [["Indicador", "Valor"]]

    for key, (valor, _) in datos_pe.items():
        tabla3_data.append([
            key,
            f"${valor:,.2f}" if "Valor" in key or "Ventas" in key else f"{valor:,.2f}"
        ])

    tabla3 = Table(tabla3_data, colWidths=[300, 150])
    tabla3.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.gray),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ]))
    
    elementos.append(tabla3)
    elementos.append(Spacer(1, 20))

    # ================
    # GRÁFICA DEL PE
    # ================
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    grafica_pe.savefig(tmp_img.name, dpi=120, bbox_inches="tight")

    tmp_img.close()

    elementos.append(Paragraph("<b>Gráfica del Punto de Equilibrio</b>", styles["Heading2"]))
    elementos.append(Image(tmp_img.name, width=450, height=300))
    elementos.append(Spacer(1, 20))

    # =================
    # GUARDAR EL PDF
    # =================
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
    doc.build(elementos)

    os.remove(tmp_img.name)
