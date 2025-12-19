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
# Usa un lock per thread-safety
conversion_status = {}
conversion_status_lock = threading.Lock()


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


def convert_task(task_id, youtube_url, audio_format):
    """Esegue la conversione in un thread separato"""
    try:
        print(f"[convert_task] Starting conversion for task_id: {task_id}")
        with conversion_status_lock:
            # Ensure task exists (should already exist from /convert endpoint, but be safe)
            if task_id not in conversion_status:
                print(f"⚠ Warning: Task {task_id} not found, creating it now")
                conversion_status[task_id] = {
                    'status': 'downloading',
                    'progress': 10,
                    'message': 'Starting download...',
                    'file': None,
                    'error': None
                }
            else:
                # Update status (task already exists from /convert endpoint)
                conversion_status[task_id].update({
                    'status': 'downloading',
                    'progress': 10,
                    'message': 'Starting download...'
                })
            print(f"[convert_task] Task {task_id} status updated, total tasks: {len(conversion_status)}")
        
        # Download video
        with conversion_status_lock:
            conversion_status[task_id].update({
                'progress': 20,
                'message': 'Downloading video...'
            })
        video_path, video_info = converter.download_video(youtube_url)
        
        with conversion_status_lock:
            conversion_status[task_id].update({
                'progress': 40,
                'message': 'Download completed'
            })
        time.sleep(0.5)  # Small pause to show message
        
        # Convert to audio
        with conversion_status_lock:
            conversion_status[task_id].update({
                'progress': 50,
                'message': 'Converting to ' + audio_format.upper() + '...'
            })
        temp_audio_path = converter.convert_to_audio(video_path, audio_format)
        
        with conversion_status_lock:
            conversion_status[task_id].update({
                'progress': 60,
                'message': 'Conversion completed'
            })
        time.sleep(0.5)
        
        # Audio analysis
        with conversion_status_lock:
            conversion_status[task_id].update({
                'progress': 70,
                'message': 'Analyzing track: BPM & key detection...'
            })
        bpm, scale = converter.analyze_audio(temp_audio_path)
        
        with conversion_status_lock:
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
        
        with conversion_status_lock:
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
        with conversion_status_lock:
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
        print("=" * 60)
        print("=== /convert endpoint called ===")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Current conversion_status size: {len(conversion_status)}")
        
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            print("ERROR: No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        youtube_url = data.get('url')
        audio_format = data.get('format', 'mp3')
        
        print(f"YouTube URL: {youtube_url}")
        print(f"Audio format: {audio_format}")
        
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
        
        # Initialize task status BEFORE starting thread
        # This ensures the task is always available for status checks
        with conversion_status_lock:
            conversion_status[task_id] = {
                'status': 'pending',
                'progress': 0,
                'message': 'Initializing conversion...',
                'file': None,
                'error': None
            }
            
            # Verify task was added (safety check)
            if task_id not in conversion_status:
                print(f"ERROR: Task {task_id} was not added to conversion_status!")
                return jsonify({"error": "Failed to initialize task"}), 500
            
            print(f"✓ Task {task_id} initialized in conversion_status (total tasks: {len(conversion_status)})")
            print(f"   Task details: {conversion_status[task_id]}")
        
        # Start conversion in separate thread
        thread = threading.Thread(target=convert_task, args=(task_id, youtube_url, audio_format))
        thread.daemon = True
        thread.start()
        
        print(f"Thread started for task_id: {task_id}")
        
        # Verify task still exists after thread start
        with conversion_status_lock:
            if task_id not in conversion_status:
                print(f"ERROR: Task {task_id} disappeared after thread start!")
                return jsonify({"error": "Task lost after thread creation"}), 500
            print(f"✓ Task {task_id} verified after thread start (total: {len(conversion_status)})")
        
        # Small delay to ensure task is fully registered before returning response
        time.sleep(0.1)
        
        # Final verification before returning
        with conversion_status_lock:
            if task_id not in conversion_status:
                print(f"ERROR: Task {task_id} disappeared before returning response!")
                return jsonify({"error": "Task lost before response"}), 500
            print(f"✓ Final check: Task {task_id} exists (total: {len(conversion_status)})")
        
        response_data = {"task_id": task_id}
        response = jsonify(response_data)
        print(f"Returning response: {response_data}")
        print("=" * 60)
        return response
    
    except Exception as e:
        error_msg = str(e)
        print(f"EXCEPTION in /convert: {error_msg}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error: {error_msg}"}), 500


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint to get conversion status"""
    with conversion_status_lock:
        print(f"Status check for task_id: {task_id}")
        print(f"Total tasks in memory: {len(conversion_status)}")
        if len(conversion_status) > 0:
            print(f"Available task IDs (first 5): {list(conversion_status.keys())[:5]}")
        
        if task_id not in conversion_status:
            print(f"⚠ Task {task_id} not found in conversion_status")
            print(f"   This could be a race condition or the task was never created")
            print(f"   Request timestamp: {time.time()}")
            print(f"   Checking if /convert was called for this task...")
            # Verifica se il task esisteva prima
            return jsonify({
                "error": "Task not found", 
                "task_id": task_id,
                "available_tasks": len(conversion_status),
                "suggestion": "The task may not have been created. Check /convert endpoint logs."
            }), 404
        
        status = conversion_status[task_id].copy()
        print(f"✓ Task {task_id} found, status: {status.get('status')}, progress: {status.get('progress')}%")
        return jsonify(status)


@app.route('/download/<task_id>', methods=['GET'])
def download_file(task_id):
    """Endpoint to download converted file"""
    with conversion_status_lock:
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
    print(f"Initial conversion_status size: {len(conversion_status)}")
    print("Ready to accept requests...")
    app.run(debug=debug, host='0.0.0.0', port=port)

