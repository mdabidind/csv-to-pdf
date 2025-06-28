from flask import Flask, request, jsonify, send_file
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os
import uuid
import datetime
import hashlib

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_file_id(ip_address, filename):
    # Create unique file ID based on IP, filename, and timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_str = f"{ip_address}-{filename}-{timestamp}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:12]

def generate_serial_number():
    # Generate an 8-character alphanumeric serial
    return uuid.uuid4().hex[:8].upper()

@app.route('/convert', methods=['POST'])
def convert_csv_to_pdf():
    # Get client IP address
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Check if file exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Generate automatic IDs
    file_id = generate_file_id(client_ip, file.filename)
    serial_number = generate_serial_number()
    
    # Save uploaded file with unique ID
    file_ext = os.path.splitext(file.filename)[1]
    upload_filename = f"{file_id}_{serial_number}{file_ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, upload_filename)
    file.save(upload_path)
    
    try:
        # Convert CSV to PDF
        output_filename = f"{file_id}_{serial_number}.pdf"
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
        
        # Create download token (expires in 1 hour)
        expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
        token_data = {
            'file_id': file_id,
            'serial': serial_number,
            'ip': client_ip,
            'expires': expiration.timestamp(),
            'filename': output_filename
        }
        
        # In production, store this in a database
        with open('tokens.txt', 'a') as f:
            f.write(f"{token_data}\n")
        
        return jsonify({
            'status': 'success',
            'file_id': file_id,
            'serial_number': serial_number,
            'download_link': f"/download/{file_id}/{serial_number}",
            'filename': output_filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>/<serial_number>', methods=['GET'])
def download_file(file_id, serial_number):
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Verify the download request
    valid = False
    output_filename = None
    
    # In production, query a database instead
    with open('tokens.txt', 'r') as f:
        for line in f:
            try:
                token_data = eval(line.strip())
                if (token_data['file_id'] == file_id and 
                    token_data['serial'] == serial_number and
                    token_data['ip'] == client_ip and
                    datetime.datetime.now().timestamp() < token_data['expires']):
                    valid = True
                    output_filename = token_data['filename']
                    break
            except:
                continue
    
    if valid and output_filename:
        filepath = os.path.join(OUTPUT_FOLDER, output_filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    
    return "Invalid or expired download link", 404

if __name__ == '__main__':
    app.run(debug=True)
