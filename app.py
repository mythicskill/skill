# Patch to provide url_quote for Flask compatibility with Werkzeug 3.x
import werkzeug.urls
if not hasattr(werkzeug.urls, "url_quote"):
    import urllib.parse
    werkzeug.urls.url_quote = urllib.parse.quote

import os
import uuid
from io import BytesIO

from flask import Flask, request, render_template_string, send_file, redirect, flash
from werkzeug.utils import secure_filename

# Import conversion modules from your package
from image_to_skill.image_processor import ImageDetails
from image_to_skill.code_generation import CodeGenerator, Mode, ParticleType

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.secret_key = 'your_secret_key'  # Replace with a secure secret in production

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# HTML content for the UI
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Image to Skill Converter</title>
</head>
<body>
  <h1>Image to Skill Converter</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul style="color: red;">
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="post" enctype="multipart/form-data">
    <div>
      <label for="image">Upload Image:</label>
      <input type="file" name="image" id="image" required>
    </div>
    <br>
    <div>
      <label for="mode">Select Mode:</label>
      <select name="mode" id="mode">
        <option value="HR">Horizontal</option>
        <option value="VT">Vertical</option>
      </select>
    </div>
    <br>
    <div>
      <label for="particle_type">Particle Type:</label>
      <input type="text" name="particle_type" id="particle_type" value="flame" required>
    </div>
    <br>
    <div>
      <label for="particle_interval">Particle Interval:</label>
      <input type="text" name="particle_interval" id="particle_interval" value="1.0" required>
    </div>
    <br>
    <div>
      <label for="particle_size">Particle Size:</label>
      <input type="text" name="particle_size" id="particle_size" value="1.0" required>
    </div>
    <br>
    <div>
      <label for="base_forward_offset">Base Forward Offset (X):</label>
      <input type="text" name="base_forward_offset" id="base_forward_offset" value="0.0" required>
    </div>
    <br>
    <div>
      <label for="base_side_offset">Base Side Offset (Y):</label>
      <input type="text" name="base_side_offset" id="base_side_offset" value="0.0" required>
    </div>
    <br>
    <div>
      <label for="base_y_offset">Base Y Offset (Z):</label>
      <input type="text" name="base_y_offset" id="base_y_offset" value="0.0" required>
    </div>
    <br>
    <button type="submit">Start Conversion</button>
  </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "image" not in request.files:
            flash("No file part")
            return redirect(request.url)
        
        file = request.files["image"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        
        # Save the uploaded image with a unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        try:
            # Create an ImageDetails instance from the uploaded image
            image_details = ImageDetails.from_path(file_path)
        except Exception as e:
            flash(f"Error processing image: {e}")
            return redirect(request.url)
        
        # Retrieve form parameters
        mode_input = request.form.get("mode", "HR")  # "HR" for Horizontal, "VT" for Vertical
        particle_type_input = request.form.get("particle_type", "flame")  # e.g., "flame"
        try:
            mode = Mode(mode_input)
            particle_type = ParticleType(particle_type_input)
        except Exception as e:
            flash(f"Error with mode or particle type: {e}")
            return redirect(request.url)
        
        try:
            particle_interval = float(request.form.get("particle_interval", "1.0"))
            particle_size = float(request.form.get("particle_size", "1.0"))
            base_forward_offset = float(request.form.get("base_forward_offset", "0.0"))
            base_side_offset = float(request.form.get("base_side_offset", "0.0"))
            base_y_offset = float(request.form.get("base_y_offset", "0.0"))
        except Exception as e:
            flash(f"Error with numeric inputs: {e}")
            return redirect(request.url)
        
        # Create the code generator instance
        generator = CodeGenerator(
            mode=mode,
            particle_type=particle_type,
            particle_interval=particle_interval,
            particle_size=particle_size,
            base_forward_offset=base_forward_offset,
            base_side_offset=base_side_offset,
            base_y_offset=base_y_offset,
            image=image_details
        )
        
        # Generate the code as a string
        output_lines = "".join(generator.generate_code())
        
        # Prepare the output as a downloadable file
        output_filename = f"{image_details.name}.yml"
        output_bytes = BytesIO(output_lines.encode("utf-8"))
        output_bytes.seek(0)
        
        return send_file(
            output_bytes,
            as_attachment=True,
            download_name=output_filename,
            mimetype="text/yaml"
        )
        
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    # Running with the built-in Flask server (good for development only)
    app.run(host="0.0.0.0", port=10000, debug=True)
