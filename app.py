from flask import Flask, request, jsonify
import joblib
from flask_cors import CORS
import googleapiclient.discovery
import re

app = Flask(__name__)
CORS(app)

# YouTube API Key
YOUTUBE_API_KEY = "AIzaSyB9G6i75d2h8fyEoweqW-N8nDSWiZejnCo"

# Load the pre-trained model
model = joblib.load('video_classifier_model5.pkl')

def extract_video_id(url):
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

def parse_iso8601_duration(duration):
    pattern = re.compile(
        r'PT'
        r'(?:(?P<hours>\d+)H)?'
        r'(?:(?P<minutes>\d+)M)?'
        r'(?:(?P<seconds>\d+)S)?'
    )
    match = pattern.fullmatch(duration)
    if not match:
        return 0
    time_data = match.groupdict()
    hours = int(time_data.get('hours') or 0)
    minutes = int(time_data.get('minutes') or 0)
    seconds = int(time_data.get('seconds') or 0)
    return hours * 3600 + minutes * 60 + seconds

def get_video_length(video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    try:
        request = youtube.videos().list(part="contentDetails", id=video_id)
        response = request.execute()
        if response and "items" in response and response["items"]:
            iso_duration = response["items"][0]["contentDetails"]["duration"]
            return parse_iso8601_duration(iso_duration)
        else:
            return None
    except Exception as e:
        print(f"YouTube API error: {e}")
        return None

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
    length = get_video_length(video_id)
    print(f'LENGTH OF THE VIDEO IS {length}')
    
    if not title:
        return jsonify({'error': 'Could not retrieve video title'}), 400
    
    print(f"Video Title: {title}")
    result = classify_title(title)
    print(f"Prediction: {result}")
    
    return jsonify({
        'result': result,
        'title': title,
        'videoId': video_id,
        'length': length  # video length in seconds
    })

if __name__ == "__main__":
    app.run(debug=True)
