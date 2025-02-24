import os
import uuid
from io import BytesIO

from flask import Flask, request, render_template, send_file, redirect, flash
from werkzeug.utils import secure_filename

# Import the conversion modules from the package
from image_to_skill.image_processor import ImageDetails
from image_to_skill.code_generation import CodeGenerator, Mode, ParticleType

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.secret_key = 'haidanh912'  # Change this in production

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
        mode_input = request.form.get("mode", "HR")  # Should be "HR" or "VT"
        particle_type_input = request.form.get("particle_type", "flame")  # Enum values (e.g., "flame")
        try:
            # Convert string inputs to appropriate enum types
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
        
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Change port if needed
