from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from converter import YouTubeAudioConverter
import traceback
import threading
import uuid
import time

app = Flask(__name__)
# Configure CORS to allow requests from any origin (for production)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Directory per file temporanei
TEMP_DIR = tempfile.gettempdir()
converter = YouTubeAudioConverter(TEMP_DIR)

# Dizionario per tracciare lo stato delle conversioni
conversion_status = {}


@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        "message": "Producer Tools - YouTube Audio Converter API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "convert": "/convert",
            "status": "/status/<task_id>",
            "download": "/download/<task_id>"
        }
    })


def convert_task(task_id, youtube_url, audio_format, cookies_content=None, browser_name=None):
    """Esegue la conversione in un thread separato"""
    try:
        conversion_status[task_id] = {
            'status': 'downloading',
            'progress': 10,
            'message': 'Starting download...',
            'file': None,
            'error': None
        }
        
        # Download video
        conversion_status[task_id].update({
            'progress': 20,
            'message': 'Downloading video...'
        })
        video_path, video_info = converter.download_video(youtube_url, cookies_content=cookies_content, browser_name=browser_name)
        
        conversion_status[task_id].update({
            'progress': 40,
            'message': 'Download completed'
        })
        time.sleep(0.5)  # Small pause to show message
        
        # Convert to audio
        conversion_status[task_id].update({
            'progress': 50,
            'message': 'Converting to ' + audio_format.upper() + '...'
        })
        temp_audio_path = converter.convert_to_audio(video_path, audio_format)
        
        conversion_status[task_id].update({
            'progress': 60,
            'message': 'Conversion completed'
        })
        time.sleep(0.5)
        
        # Audio analysis
        conversion_status[task_id].update({
            'progress': 70,
            'message': 'Analyzing track: BPM & key detection...'
        })
        bpm, scale = converter.analyze_audio(temp_audio_path)
        
        conversion_status[task_id].update({
            'progress': 85,
            'message': 'Analysis completed'
        })
        time.sleep(0.5)
        
        # Genera nome file e rinomina
        title = video_info.get('title', 'Track')
        custom_filename = converter.generate_filename(title, bpm, scale, audio_format)
        final_output_path = os.path.join(converter.temp_dir, custom_filename)
        
        if os.path.exists(temp_audio_path):
            if os.path.exists(final_output_path):
                os.remove(final_output_path)
            os.rename(temp_audio_path, final_output_path)
        
        # Pulisce file video temporaneo
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass
        
        conversion_status[task_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Ready for download',
            'file': final_output_path
        })
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error during conversion: {error_msg}")
        print(traceback.format_exc())
        conversion_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': 'Error during conversion',
            'error': error_msg,
            'file': None
        }


@app.route('/convert', methods=['POST'])
def convert():
    """Endpoint to start conversion (returns task_id)"""
    try:
        print("=== /convert endpoint called ===")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            print("ERROR: No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        youtube_url = data.get('url')
        audio_format = data.get('format', 'mp3')
        cookies_content = data.get('cookies')  # Optional cookies content
        browser_name = data.get('browser')  # Optional browser name for cookie extraction
        
        print(f"YouTube URL: {youtube_url}")
        print(f"Audio format: {audio_format}")
        print(f"Cookies provided: {bool(cookies_content)}")
        print(f"Browser for cookies: {browser_name if browser_name else 'None'}")
        
        if not youtube_url:
            print("ERROR: YouTube URL missing")
            return jsonify({"error": "YouTube URL missing"}), 400
        
        # Format validation
        valid_formats = ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'opus']
        if audio_format not in valid_formats:
            print(f"ERROR: Unsupported format: {audio_format}")
            return jsonify({"error": f"Unsupported format. Valid formats: {', '.join(valid_formats)}"}), 400
        
        # Generate unique task_id
        task_id = str(uuid.uuid4())
        print(f"Generated task_id: {task_id}")
        
        # Start conversion in separate thread
        thread = threading.Thread(target=convert_task, args=(task_id, youtube_url, audio_format, cookies_content, browser_name))
        thread.daemon = True
        thread.start()
        
        print(f"Thread started for task_id: {task_id}")
        response_data = {"task_id": task_id}
        response = jsonify(response_data)
        print(f"Returning response: {response_data}")
        return response
    
    except Exception as e:
        error_msg = str(e)
        print(f"EXCEPTION in /convert: {error_msg}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error: {error_msg}"}), 500


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint to get conversion status"""
    if task_id not in conversion_status:
        return jsonify({"error": "Task not found"}), 404
    
    status = conversion_status[task_id].copy()
    return jsonify(status)


@app.route('/download/<task_id>', methods=['GET'])
def download_file(task_id):
    """Endpoint to download converted file"""
    if task_id not in conversion_status:
        return jsonify({"error": "Task not found"}), 404
    
    status = conversion_status[task_id]
    
    if status['status'] != 'completed' or not status.get('file'):
        return jsonify({"error": "File not ready yet"}), 400
    
    file_path = status['file']
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path),
        mimetype='application/octet-stream'
    )


@app.route('/health', methods=['GET'])
def health():
    """Endpoint per verificare lo stato del server"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    # Check if ffmpeg is available
    print("Checking for ffmpeg...")
    if not converter.check_ffmpeg():
        print("ERROR: ffmpeg not found. Make sure it's installed on the system.")
        exit(1)
    print("✓ ffmpeg found")
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Server starting on http://0.0.0.0:{port}")
    print(f"Debug mode: {debug}")
    print("Ready to accept requests...")
    app.run(debug=debug, host='0.0.0.0', port=port)

