from flask import Flask, request, jsonify
import joblib
from flask_cors import CORS
import googleapiclient.discovery
import re


app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# YouTube API Key
YOUTUBE_API_KEY = "AIzaSyB9G6i75d2h8fyEoweqW-N8nDSWiZejnCo"

# Load the pre-trained model
model = joblib.load('video_classifier_model5.pkl')

# Function to extract video ID from YouTube URL
def extract_video_id(url):
    # Pattern to match YouTube video URLs
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\s]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^\?\s]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^\?\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Function to get video title from YouTube API
def get_video_title(video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response and "items" in response and response["items"]:
            return response["items"][0]["snippet"]["title"]
        else:
            return None
    except Exception as e:
        print(f"YouTube API error: {e}")
        return None

# Function to classify a video title
def classify_title(title):
    prediction = model.predict([title])
    return prediction[0]

@app.route('/classify', methods=['POST'])
def classify_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    title = get_video_title(video_id)
    if not title:
        return jsonify({'error': 'Could not retrieve video title'}), 400
    
    print(f"Video Title: {title}")
    result = classify_title(title)
    print(f"Prediction: {result}")
    
    return jsonify({
        'result': result,
        'title': title,
        'videoId': video_id
    })

if __name__ == "__main__":
    app.run(debug=True)