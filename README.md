# 🔍 Forensic Metadata Extractor

A web-based application built using Python (Flask) that extracts metadata from files like images, PDFs, and documents.  
This project is useful in digital forensics and data analysis.

---

## 🚀 Features

- 📂 Upload files (JPG, PNG, PDF, DOCX)
- 🧾 Extract metadata (author, title, resolution, etc.)
- 📍 GPS coordinates detection from images
- 🖼️ JPEG thumbnail extraction
- 🔍 Search stored metadata
- 💾 Data stored in SQLite database

---

## 🛠️ Tech Stack

- Python (Flask)
- HTML, CSS
- SQLite
- Pillow (Image processing)
- python-docx
- PyPDF2

---

## 📁 Project Structure

forensic-app/
│
├── app.py
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
└── uploads/   (NOT pushed to GitHub)

---

## ⚙️ Installation

1. Clone the repository:
git clone https://github.com/your-username        forensic-app.git⁠� cd forensic-app

2. Install dependencies:
pip install flask pillow python-docx PyPDF2

3. Run the app:
python app.py

4. Open in browser:
http://127.0.0.1:5000

---

## 📸 Example Output

- Image metadata (Resolution, Orientation)
- GPS coordinates (if available)
- Document properties (Author, Title)

---

## 🔒 Use Case

- Digital Forensics
- File investigation
- Metadata analysis

---

## 👨‍💻 Author

Shreyansh Singh

---

## ⭐ Future Improvements

- AI-based file analysis
- File type classification
- Dashboard with graphs
