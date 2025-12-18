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
CORS(app)  # Permette richieste cross-origin dal frontend

# Directory per file temporanei
TEMP_DIR = tempfile.gettempdir()
converter = YouTubeAudioConverter(TEMP_DIR)

# Dizionario per tracciare lo stato delle conversioni
conversion_status = {}


@app.route('/')
def index():
    """Redirect alla pagina principale"""
    return jsonify({"message": "YouTube Audio Converter API"})


def convert_task(task_id, youtube_url, audio_format):
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
        video_path, video_info = converter.download_video(youtube_url)
        
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
    """Endpoint per avviare la conversione (restituisce task_id)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Nessun dato fornito"}), 400
        
        youtube_url = data.get('url')
        audio_format = data.get('format', 'mp3')
        
        if not youtube_url:
            return jsonify({"error": "URL YouTube mancante"}), 400
        
        # Validazione formato
        valid_formats = ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'opus']
        if audio_format not in valid_formats:
            return jsonify({"error": f"Formato non supportato. Formati validi: {', '.join(valid_formats)}"}), 400
        
        # Genera un task_id univoco
        task_id = str(uuid.uuid4())
        
        # Avvia la conversione in un thread separato
        thread = threading.Thread(target=convert_task, args=(task_id, youtube_url, audio_format))
        thread.daemon = True
        thread.start()
        
        return jsonify({"task_id": task_id})
    
    except Exception as e:
        error_msg = str(e)
        print(f"Errore: {error_msg}")
        print(traceback.format_exc())
        return jsonify({"error": f"Errore: {error_msg}"}), 500


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint per ottenere lo stato della conversione"""
    if task_id not in conversion_status:
        return jsonify({"error": "Task non trovato"}), 404
    
    status = conversion_status[task_id].copy()
    return jsonify(status)


@app.route('/download/<task_id>', methods=['GET'])
def download_file(task_id):
    """Endpoint per scaricare il file convertito"""
    if task_id not in conversion_status:
        return jsonify({"error": "Task non trovato"}), 404
    
    status = conversion_status[task_id]
    
    if status['status'] != 'completed' or not status.get('file'):
        return jsonify({"error": "File non ancora pronto"}), 400
    
    file_path = status['file']
    if not os.path.exists(file_path):
        return jsonify({"error": "File non trovato"}), 404
    
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
    # Verifica che ffmpeg sia disponibile
    if not converter.check_ffmpeg():
        print("ERRORE: ffmpeg non trovato. Assicurati che sia installato sul sistema.")
        exit(1)
    
    print("Server avviato su http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

