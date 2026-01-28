from flask import Flask, render_template, request, send_file
from PIL import Image
import os

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

UPLOAD_FOLDER = "/tmp/uploads"   # REQUIRED for Vercel
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

END_MARKER = "1111111111111110"

# ---------- STEGANOGRAPHY FUNCTIONS ----------

def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text) + END_MARKER

def encode_image(image_path, message, output_path):
    img = Image.open(image_path).convert("RGB")
    pixels = img.load()
    binary_msg = text_to_binary(message)
    idx = 0

    for y in range(img.height):
        for x in range(img.width):
            if idx >= len(binary_msg):
                img.save(output_path)
                return
            r, g, b = pixels[x, y]
            r = (r & ~1) | int(binary_msg[idx]); idx += 1
            if idx < len(binary_msg):
                g = (g & ~1) | int(binary_msg[idx]); idx += 1
            if idx < len(binary_msg):
                b = (b & ~1) | int(binary_msg[idx]); idx += 1
            pixels[x, y] = (r, g, b)

    img.save(output_path)

def decode_image(image_path):
    img = Image.open(image_path)
    pixels = img.load()
    binary_data = ""

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)
            if END_MARKER in binary_data:
                binary_data = binary_data.replace(END_MARKER, "")
                return ''.join(
                    chr(int(binary_data[i:i+8], 2))
                    for i in range(0, len(binary_data), 8)
                )
    return "No hidden message found"

# ---------- ROUTE ----------

@app.route("/", methods=["GET", "POST"])
def index():
    decoded_message = ""

    if request.method == "POST":
        action = request.form["action"]

        if action == "encode":
            image = request.files["encode_image"]
            message = request.form["message"]

            in_path = os.path.join(UPLOAD_FOLDER, image.filename)
            out_path = os.path.join(UPLOAD_FOLDER, "encrypted.png")

            image.save(in_path)
            encode_image(in_path, message, out_path)

            return send_file(out_path, as_attachment=True)

        elif action == "decode":
            image = request.files["decode_image"]
            path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(path)
            decoded_message = decode_image(path)

    return render_template("index.html", decoded_message=decoded_message)

# 🔑 THIS LINE IS IMPORTANT FOR VERCEL
def handler(event, context):
    return app(event, context)
