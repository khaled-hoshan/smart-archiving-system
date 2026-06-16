import os
import cv2
import numpy as np
import easyocr
import datetime
from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    redirect,
    url_for,
    jsonify,
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# --- SETTINGS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "captures")
PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")
ADMIN_PASSWORD = "123"

for folder in [UPLOAD_FOLDER, PDF_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

print("🔄 Loading EasyOCR (This takes a moment)...")
reader = easyocr.Reader(["en"], gpu=False)
print("✅ Brain is Ready!")


# --- AI PROCESSING LOGIC ---
def process_and_create_pdf(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image from {image_path}")
    # 1. Clean Image (Shadow Removal)
    rgb_planes = cv2.split(img)
    result_planes = []
    for plane in rgb_planes:
        dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg = cv2.medianBlur(dilated, 21)
        diff = 255 - cv2.absdiff(plane, bg)
        result_planes.append(diff)
    shadow_free = cv2.merge(result_planes)

    # 2. Save Cleaned Image
    cleaned_path = image_path.replace(".jpg", "_cleaned.jpg")
    cv2.imwrite(cleaned_path, shadow_free)

    # 3. OCR
    results = reader.readtext(image_path)
    extracted_text = "\n".join([text for _, text, conf in results if float(conf) > 0.3])

    # 4. Create PDF
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = f"lecture_{timestamp}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, pdf_name)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Smart Archive Lecture")
    c.drawImage(cleaned_path, 50, 350, width=500, preserveAspectRatio=True)
    c.setFont("Helvetica", 10)
    text_obj = c.beginText(50, 320)
    for line in extracted_text.split("\n")[:15]:  # Limit lines to fit page
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.save()
    return pdf_name


# --- ROUTES ---
@app.route("/")
def index():
    files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file", 400
    file = request.files["file"]
    save_path = os.path.join(UPLOAD_FOLDER, "latest.jpg")
    file.save(save_path)

    # Trigger the AI
    pdf_generated = process_and_create_pdf(save_path)
    print(f"✅ AI Processed new image: {pdf_generated}")
    return jsonify({"status": "processed", "pdf": pdf_generated})


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename)


@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if request.form.get("password") == ADMIN_PASSWORD:
        file_path = os.path.join(PDF_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
