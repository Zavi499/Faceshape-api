from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Header
from keras.models import load_model
from keras.preprocessing import image
from datetime import datetime, date
from collections import defaultdict
import numpy as np
import logging
import gc
import os
import uvicorn
from io import BytesIO
import cv2
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Load the trained model
model = load_model("face_shape_classifier.h5")

# Load OpenCV's pre-trained Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Define FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "https://faceshapesdetectors.com",
    "http://127.0.0.1:8000",  # Replace with your WordPress domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key for authentication
API_KEY = "zavinomanarslan420"

# Initialize a dictionary to store API call counts
api_call_count = defaultdict(int)


@app.middleware("http")
async def count_requests(request: Request, call_next):
    # Get the current date
    today = date.today()

    # Increment the count for today's date
    api_call_count[today] += 1

    # Proceed with the request
    response = await call_next(request)
    return response


@app.get("/api/call_count/")
async def get_api_call_count():
    # Return the count for today
    today = date.today()
    count = api_call_count[today]
    return {"date": today.isoformat(), "api_calls": count}


# Define a function to preprocess the image
def preprocess_image(file):
    # Convert the SpooledTemporaryFile to a BytesIO object
    image_stream = BytesIO(
        file.read()
    )  # Read the content and wrap it in a BytesIO object

    # Load and preprocess the image from the BytesIO stream
    img = image.load_img(image_stream, target_size=(160, 160))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0  # Normalize the image
    return img_array


# Define a function to detect faces in an image
def detect_face(image_bytes):
    # Convert BytesIO image to OpenCV format
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )
    del img, gray

    return len(faces) > 0

# Head Endpoint
@app.head("/predict/")
async def predict_head():
    return {"message": "API is Live"}


# Define endpoint for predicting face shape from uploaded image
@app.post("/predict/")
async def predict_face_shape(
    file: UploadFile = File(...),
    x_api_key: str = Header(...),  # API Key header
):
    # Validate the API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    # Validate that the uploaded file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an image."
        )

    try:
        # Check if the image contains a face
        image_bytes = file.file.read()
        if not detect_face(image_bytes):
            del image_bytes
            gc.collect()
            return {
                "message": "No Face Detected, Please Upload an image with clear Face"
            }

        # Rewind the file stream to the beginning for further processing
        file.file.seek(0)

        # Preprocess the image
        img_array = preprocess_image(file.file)

        # Make prediction
        predictions = model.predict(img_array)[0]

        # Define class labels
        class_labels = ["heart", "oblong", "oval", "round", "square"]

        # Create and sort response dictionary in descending order of prediction probabilities
        response = {
            class_labels[i]: f"{predictions[i] * 100:.2f}%"
            for i in range(len(class_labels))
        }
        sorted_response = dict(
            sorted(response.items(), key=lambda item: float(item[1][:-1]), reverse=True)
        )

        return sorted_response
    except Exception as e:
        logging.error(f"Error in prediction: {str(e)}")
        return {"error": "An error occurred during prediction. Please try again."}
    finally:
        # Close the file to release resources
        file.file.close()

# Run the FastAPI server
if __name__ == "__main__":
    uvicorn.run(
        app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), workers=2
    )