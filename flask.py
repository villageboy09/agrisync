from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)

# Set the environment variable for API key
os.environ["API_KEY"] = "AIzaSyCroPtzjFYNxHBuf_f-S_10cxu-B9TBhQI"

# Configure the API
api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("API key is not set in environment variables.")
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

# Define supported crops
SUPPORTED_CROPS = [
    "tomato", "chilli", "paddy", "pearl millet", 
    "sorghum", "wheat", "maize", "groundnut", 
    "soybean", "sugarcane"
]

# Function to process the image using PIL
def process_image_with_pil(image_file):
    # Open image using PIL
    image = Image.open(image_file).convert("RGB")
    
    # Example processing: Convert to grayscale
    processed_image = image.convert("L")
    
    return processed_image

# Function to upload an image using File API
def upload_image(image_file):
    try:
        # Process the image with PIL
        processed_image = process_image_with_pil(image_file)
        
        # Save the processed image to a temporary file
        temp_path = '/tmp/temp_image.png'
        processed_image.save(temp_path)

        # Upload the image using File API
        response = genai.upload_file(path=temp_path, display_name="Processed Image")
        return response.uri
    except Exception as e:
        raise RuntimeError(f"Error uploading image: {e}")

# Function to analyze image and get recommendations
def analyze_image(image_uri):
    try:
        # Create a prompt based on supported crops
        prompt = (
            "Identify any crop diseases from the uploaded image and provide recommendations for the following crops: "
            + ", ".join(SUPPORTED_CROPS) + "."
        )
        response = model.generate_content([image_uri, prompt])
        return response.text
    except Exception as e:
        raise RuntimeError(f"Error analyzing image: {e}")

@app.route('/upload', methods=['POST'])
def upload_and_analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        try:
            # Save the uploaded file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join('/tmp', filename)
            file.save(file_path)
            
            # Upload and analyze image
            image_uri = upload_image(file_path)
            if image_uri:
                recommendations = analyze_image(image_uri)
                return jsonify({"recommendations": recommendations}), 200
            else:
                return jsonify({"error": "Failed to upload image. Please try again."}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
