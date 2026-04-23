from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sqlite3
import exifread
from PIL import Image
from PyPDF2 import PdfReader
import docx
import hashlib
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filetype TEXT,
        metadata TEXT,
        extracted_text TEXT,
        file_hash TEXT UNIQUE,
        gps_lat REAL,
        gps_lon REAL,
        date_extracted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_to_db(filename, ext, metadata, text, file_hash, lat=None, lon=None):
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO metadata_records 
        (filename, filetype, metadata, extracted_text, file_hash, gps_lat, gps_lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filename, ext, metadata, text, file_hash, lat, lon))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Duplicate file detected")
    conn.close()

# ---------------- HASH ----------------
def get_file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# ---------------- GPS ----------------
def dms_to_decimal(dms, ref):
    degrees = dms.values[0].num / dms.values[0].den
    minutes = dms.values[1].num / dms.values[1].den
    seconds = dms.values[2].num / dms.values[2].den
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal *= -1
    return decimal

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    metadata_str = ""
    extracted_text = ""
    lat, lon = None, None
    file_hash = get_file_hash(filepath)

    try:
        extracted_text =""
        lat, lon =None, None

        # -------- IMAGE --------
        if ext in ['.jpg', '.jpeg', '.png']:
            image = Image.open(filepath)

            extracted_text = pytesseract.image_to_string(image)

            with open(filepath, 'rb') as f:
              tags = exifread.process_file(f)

            
            if 'JPEGThumbnail' in tags:
                thumb = tags['JPEGThumbnail']
                with open('thumb.jpg', 'wb') as f:
                     f.write(thumb)

            exif_data = {str(tag): str(tags[tag]) for tag in tags}

            fields = exif_data
            fields['Format'] = image.format
            fields['Size'] = image.size

            metadata_str = str(fields)

            if ext in ['.jpg', '.jpeg']:
                with open(filepath, 'rb') as f:
                    tags = exifread.process_file(f)

                gps_lat = tags.get('GPS GPSLatitude')
                gps_lat_ref = tags.get('GPS GPSLatitudeRef')
                gps_lon = tags.get('GPS GPSLongitude')
                gps_lon_ref = tags.get('GPS GPSLongitudeRef')

                if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
                    lat = dms_to_decimal(gps_lat, str(gps_lat_ref))
                    lon = dms_to_decimal(gps_lon, str(gps_lon_ref))

            result = {'type': 'IMAGE', 'fields': fields, 'gps': {'lat': lat, 'lon': lon},'text':extracted_text}

        # -------- PDF --------
        elif ext == '.pdf':
            reader = PdfReader(filepath)
            meta = reader.metadata or {}

            for page in reader.pages:
                extracted_text += page.extract_text() or ""

            fields = {str(k): str(v) for k, v in meta.items()}
            metadata_str = str(fields)

            result = {'type': 'PDF', 'fields': fields, 'gps': None,'text':extracted_text}

        # -------- DOCX --------
        elif ext == '.docx':
            doc_obj = docx.Document(filepath)
            cp = doc_obj.core_properties

            extracted_text = "\n".join([p.text for p in doc_obj.paragraphs])

            fields = {
                'Author': str(cp.author),
                'Title': str(cp.title),
            }

            metadata_str = str(fields)
            result = {'type': 'DOCX', 'fields': fields, 'gps': None,'text':extracted_text}

        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        print("Text Saved:", extracted_text[:100])
        save_to_db(file.filename, ext, metadata_str, extracted_text, file_hash, lat, lon)

        return jsonify({'success': True, **result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------- SEARCH --------
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')

    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT filename, filetype, extracted_text 
    FROM metadata_records 
    WHERE extracted_text LIKE ?
    """, ('%' + query + '%',))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            'filename': r[0],
            'filetype': r[1],
            'preview': (r[2] or "")[:200]
        })

    return jsonify(results)

# -------- RECORDS --------
@app.route('/records', methods=['GET'])
def records():
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, filetype, gps_lat, gps_lon, date_extracted FROM metadata_records ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            'id': r[0],
            'filename': r[1],
            'filetype': r[2],
            'gps_lat': r[3],
            'gps_lon': r[4],
            'date_extracted': r[5]
        }
        for r in rows
    ])

# -------- RUN --------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)