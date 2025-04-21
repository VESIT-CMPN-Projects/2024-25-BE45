import os
from werkzeug.utils import secure_filename
from flask import Blueprint, send_from_directory, request, render_template
from services.services_batch import parse_system_report, get_driver_links

batch_bp = Blueprint('batch', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@batch_bp.route('/')
def home():
    return render_template('batch_tool.html')

@batch_bp.route('/download_batch')
def download_batch():
    return send_from_directory('static', 'collect_system_info.bat', as_attachment=True)

@batch_bp.route('/upload_output', methods=['POST'])
def upload_output():
    if 'output_file' not in request.files:
        return 'No file part', 400

    file = request.files['output_file']
    
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        parsed_info = parse_system_report(file_path)

        driver_links = get_driver_links(parsed_info)
        
        return render_template('system_report.html', parsed_info=parsed_info, driver_links=driver_links)
    
    return 'Invalid file type', 400
