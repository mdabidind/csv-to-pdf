# server.py
from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os
import uuid
import datetime
import hashlib
import threading

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_file_id(ip_address, filename):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_str = f"{ip_address}-{filename}-{timestamp}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:12]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_csv_to_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    try:
        client_ip = request.remote_addr
        file_id = generate_file_id(client_ip, file.filename)
        serial_number = uuid.uuid4().hex[:8].upper()
        
        # Save uploaded file
        upload_filename = f"{file_id}_{serial_number}.csv"
        upload_path = os.path.join(UPLOAD_FOLDER, upload_filename)
        file.save(upload_path)
        
        # Convert to PDF
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
        
        return jsonify({
            'status': 'success',
            'file_id': file_id,
            'serial_number': serial_number,
            'download_link': f"/download/{output_filename}",
            'filename': output_filename
        })
        
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'Empty CSV file'}), 400
    except pd.errors.ParserError:
        return jsonify({'error': 'Invalid CSV format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    # Create necessary folders
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Write the HTML template if it doesn't exist
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>CSV to PDF Converter</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>CSV to PDF Converter</h1>
        <div class="upload-box">
            <input type="file" id="csvFile" accept=".csv">
            <button onclick="uploadFile()">Convert</button>
        </div>
        <div id="status"></div>
        <div id="download-section" style="display:none;">
            <a id="download-link" href="#" download>
                <button>Download PDF</button>
            </a>
        </div>
    </div>
    <script src="/static/script.js"></script>
</body>
</html>""")
    
    # Write the CSS file if it doesn't exist
    if not os.path.exists('static/style.css'):
        with open('static/style.css', 'w') as f:
            f.write("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}
.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.upload-box {
    margin: 20px 0;
    padding: 20px;
    border: 2px dashed #ccc;
    text-align: center;
}
button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    cursor: pointer;
    border-radius: 4px;
}
button:hover {
    background-color: #45a049;
}
#status {
    margin: 20px 0;
    padding: 10px;
    border-radius: 4px;
}
.error {
    background-color: #ffebee;
    color: #c62828;
}
.success {
    background-color: #e8f5e9;
    color: #2e7d32;
}""")
    
    # Write the JavaScript file if it doesn't exist
    if not os.path.exists('static/script.js'):
        with open('static/script.js', 'w') as f:
            f.write("""async function uploadFile() {
    const fileInput = document.getElementById('csvFile');
    const statusDiv = document.getElementById('status');
    const downloadSection = document.getElementById('download-section');
    
    if (!fileInput.files.length) {
        statusDiv.className = 'error';
        statusDiv.innerHTML = 'Please select a CSV file';
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.csv')) {
        statusDiv.className = 'error';
        statusDiv.innerHTML = 'Please upload a CSV file';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        statusDiv.className = '';
        statusDiv.innerHTML = 'Processing...';
        downloadSection.style.display = 'none';
        
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            statusDiv.className = 'error';
            statusDiv.innerHTML = data.error;
        } else {
            statusDiv.className = 'success';
            statusDiv.innerHTML = 'Conversion successful!';
            
            const downloadLink = document.getElementById('download-link');
            downloadLink.href = data.download_link;
            downloadLink.download = data.filename;
            downloadSection.style.display = 'block';
        }
    } catch (error) {
        statusDiv.className = 'error';
        statusDiv.innerHTML = 'Error: ' + error.message;
        console.error(error);
    }
}""")
    
    # Start the Flask server
    start_flask()
