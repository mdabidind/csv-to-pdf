import sys
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def convert_csv_to_pdf(doc_id):
    input_path = f'inputs/{doc_id}.csv'
    output_path = f'outputs/{doc_id}.pdf'
    
    # Read CSV
    df = pd.read_csv(input_path)
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    
    # Convert DataFrame to list of lists for ReportLab
    data = [df.columns.values.tolist()] + df.values.tolist()
    
    # Create table
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)

if __name__ == "__main__":
    doc_id = sys.argv[1]
    convert_csv_to_pdf(doc_id)
