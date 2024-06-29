import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import qrcode
from PIL import Image, ImageColor, ImageDraw
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.secret_key = 'supersecretkey'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def list_uploaded_images():
    return [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]

def create_qr_code(data, fill_color="black", back_color="white", image_path=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=ImageColor.getcolor(fill_color, "RGBA"), back_color=ImageColor.getcolor(back_color, "RGBA")).convert("RGBA")

    if image_path:
        img = embed_image(img, image_path)

    return img

def embed_image(qr_img, image_path):
    icon = Image.open(image_path)
    qr_width, qr_height = qr_img.size
    icon_size = qr_width // 4  # Decrease the size of the icon

    icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    # Create a circular mask
    mask = Image.new('L', (icon_size, icon_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, icon_size, icon_size), fill=255)

    # Apply the circular mask to the icon
    icon = icon.convert("RGBA")
    icon.putalpha(mask)

    icon_pos = ((qr_width - icon_size) // 2, (qr_height - icon_size) // 2)

    qr_img.paste(icon, icon_pos, mask=icon)

    return qr_img

@app.route('/')
def index():
    images = list_uploaded_images()
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File successfully uploaded')
        return redirect(url_for('index'))
    else:
        flash('Allowed file types are png, jpg, jpeg')
        return redirect(request.url)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form.get('data')
    fill_color = request.form.get('fill_color', 'black')
    back_color = request.form.get('back_color', 'white')
    selected_image = request.form.get('selected_image')
    image_path = None

    if selected_image and selected_image != 'None':
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_image)

    img = create_qr_code(data, fill_color, back_color, image_path)

    byte_io = io.BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)

    return send_file(byte_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
