from flask import Flask, request, jsonify, send_file
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os
import uuid
import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_download_link(ip, serial, filename):
    # Generate unique token
    token = str(uuid.uuid4())
    # Store mapping (in production use a database)
    with open('tokens.txt', 'a') as f:
        f.write(f"{token},{ip},{serial},{filename},{datetime.datetime.now()}\n")
    return f"https://yourdomain.com/download?token={token}"

@app.route('/convert', methods=['POST'])
def convert_csv_to_pdf():
    # Get client IP and serial
    client_ip = request.remote_addr
    serial_number = request.form.get('serial')
    
    # Check if file exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save uploaded file
    upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(upload_path)
    
    try:
        # Convert CSV to PDF
        output_filename = f"{os.path.splitext(file.filename)[0]}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        df = pd.read_csv(upload_path)
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        data = [df.columns.values.tolist()] + df.values.tolist()
        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), '#CCCCCC'),
            ('TEXTCOLOR', (0,0), (-1,0), '#000000'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, '#000000')
        ])
        table.setStyle(style)
        doc.build([table])
        
        # Generate download link
        download_link = generate_download_link(client_ip, serial, output_filename)
        
        return jsonify({
            'status': 'success',
            'download_link': download_link,
            'filename': output_filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_file():
    token = request.args.get('token')
    
    # Verify token (in production use a database)
    with open('tokens.txt', 'r') as f:
        for line in f:
            stored_token, ip, serial, filename, timestamp = line.strip().split(',')
            if stored_token == token:
                # Verify IP matches (optional)
                if ip == request.remote_addr:
                    filepath = os.path.join(OUTPUT_FOLDER, filename)
                    if os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True)
    
    return "Invalid or expired download link", 404

if __name__ == '__main__':
    app.run(debug=True)
