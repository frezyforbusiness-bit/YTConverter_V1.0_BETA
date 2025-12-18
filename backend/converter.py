import os
import subprocess
import yt_dlp
import tempfile
from pathlib import Path
import re
import librosa
import numpy as np
import uuid


class YouTubeAudioConverter:
    """Classe per convertire video YouTube in file audio"""
    
    def __init__(self, temp_dir=None):
        """
        Inizializza il converter
        
        Args:
            temp_dir: Directory per file temporanei (default: tempfile.gettempdir())
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.ensure_temp_dir()
    
    def ensure_temp_dir(self):
        """Assicura che la directory temporanea esista"""
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def check_ffmpeg(self):
        """Verifica che ffmpeg sia installato e disponibile"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def validate_youtube_url(self, url):
        """Valida che l'URL sia un link YouTube valido"""
        # Rifiuta esplicitamente gli URL di playlist (non video singoli con parametro list=)
        if '/playlist' in url.lower():
            raise ValueError("Le playlist non sono supportate. Inserisci l'URL di un singolo video.")
        
        # Verifica che sia un URL YouTube valido
        youtube_pattern = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        if not youtube_pattern.match(url):
            raise ValueError("URL YouTube non valido")
        
        return True
    
    def download_video(self, youtube_url, get_info_only=False):
        """
        Downloads YouTube video as temporary file or extracts info only.
        
        Production-ready implementation for Docker/VPS/Render:
        - Headless operation (no browser dependencies)
        - Robust retry logic with multiple player clients
        - Clear error messages for REST API
        
        Args:
            youtube_url: YouTube video URL
            get_info_only: If True, only extracts metadata without downloading
        
        Returns:
            tuple: (video_path, video_info) if get_info_only=False
                   (None, video_info) if get_info_only=True
        
        Raises:
            ValueError: Invalid URL or playlist detected
            FileNotFoundError: Video file not found after download
            Exception: Download failed after trying all clients (with clear error message)
        """
        # Validate URL first
        if not self.validate_youtube_url(youtube_url):
            raise ValueError("Invalid YouTube URL")
        
        # Base yt-dlp configuration (production-ready, headless)
        base_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'noplaylist': True,
            'extract_flat': False,
            
            # Modern user agent (helps avoid basic bot detection)
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Realistic HTTP headers (mimics real browser)
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            },
            
            # Retry configuration (robust against temporary failures)
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 5,
            'socket_timeout': 30,
            'concurrent_fragments': 1,  # Reduce concurrent requests to avoid detection
            
            # Anti-bot options
            'geo_bypass': True,
            'age_limit': None,
            
            # Security options
            'no_check_certificate': False,
            'prefer_insecure': False,
            'prefer_free_formats': False,
            
            # Additional options to help with extraction
            'ignoreerrors': False,
            'no_warnings': False,
        }
        
        # Player clients to try in priority order (iOS → Android → Web)
        # iOS client is least blocked, web client is most compatible
        player_clients = [
            ['ios'],      # Priority 1: Mobile iOS client (least blocked)
            ['android'],  # Priority 2: Mobile Android client
            ['web'],      # Priority 3: Standard web client
            ['mweb'],     # Priority 4: Mobile web client (fallback)
        ]
        
        video_path = None
        last_error = None
        last_client = None
        
        # Try each player client in order
        for client_list in player_clients:
                try:
                    # Build options for this client
                    current_opts = base_opts.copy()
                    current_opts['extractor_args'] = {
                        'youtube': {
                            'player_client': client_list,
                            'player_skip': ['webpage', 'configs'],  # Skip unnecessary data
                        }
                    }
                    
                    # Small delay between retries to avoid rate limiting
                    if last_error:
                        import time
                        time.sleep(1.0)  # Increased delay to avoid rate limiting
                    
                    print(f"Trying player client: {client_list[0]}")
                    
                    # Extract info first (validates URL and checks for playlists)
                    with yt_dlp.YoutubeDL(current_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=False)
                    
                    # Validate: reject playlists
                    if info.get('_type') == 'playlist':
                        raise ValueError("Playlists are not supported. Use a single video URL.")
                    
                    # Handle single-entry playlists (YouTube sometimes returns this)
                    if 'entries' in info and info['entries']:
                        entries = list(info['entries'])
                        if len(entries) > 1:
                            raise ValueError("Playlists are not supported. Use a single video URL.")
                        if len(entries) == 1:
                            info = entries[0]
                    
                    # Validate video ID
                    if not info.get('id'):
                        raise ValueError("Unable to extract video information. Check that the URL is correct.")
                    
                    # If only info is needed, return now
                    if get_info_only:
                        return None, info
                    
                    # Download the video
                    with yt_dlp.YoutubeDL(current_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=True)
                        video_path = ydl.prepare_filename(info)
                    
                    # Handle different file extensions (yt-dlp may download with different extension)
                    if not os.path.exists(video_path):
                        base_name = os.path.splitext(video_path)[0]
                        for ext in ['.webm', '.m4a', '.mp4', '.opus', '.ogg']:
                            potential_path = base_name + ext
                            if os.path.exists(potential_path):
                                video_path = potential_path
                                break
                    
                    # Final validation
                    if not os.path.exists(video_path):
                        raise FileNotFoundError("Video file not found after download")
                    
                    # Success!
                    print(f"Successfully downloaded using client: {client_list[0]}")
                    return video_path, info
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = e
                    last_client = client_list[0]
                    print(f"Client {client_list[0]} failed: {error_msg[:100]}...")
                    
                    # Don't retry on playlist errors (user error)
                    if 'playlist' in error_msg.lower():
                        raise ValueError("Playlists are not supported. Use a single video URL.")
                    
                    # Continue to next client for other errors
                    continue
        
        # All clients failed - provide clear error message
        if last_error:
            error_msg = str(last_error)
            self._raise_download_error(error_msg)
        else:
            raise Exception("Failed to download video: Unknown error")
    
    def _raise_download_error(self, error_msg):
        """
        Raises appropriate exception with clear error message based on error type.
        
        Args:
            error_msg: Original error message from yt-dlp
        """
        error_lower = error_msg.lower()
        
        # Bot detection / authentication required
        if 'bot' in error_lower or 'sign in' in error_lower:
            raise Exception("YouTube is blocking the request. This video may require authentication or the service is temporarily unavailable. Please try again later or use a different video.")
        
        # Player response extraction failed (most common error)
        elif ('player response' in error_lower or 
              'failed to extract' in error_lower or 
              'failed to parse json' in error_lower or
              'unable to extract player version' in error_lower):
            raise Exception("Failed to extract player response from YouTube. This might be due to YouTube restrictions or the video being unavailable. Please try again later or use a different video.")
        
        # Generic error
        else:
            raise Exception(f"YouTube download failed: {error_msg}. Please try again later or use a different video.")
    
    def convert_to_audio(self, video_path, audio_format, output_path=None):
        """
        Converte il video in formato audio specificato
        
        Args:
            video_path: Path del file video
            audio_format: Formato audio desiderato (mp3, wav, flac, ogg, m4a, opus)
            output_path: Path di output (opzionale, generato automaticamente se None)
        
        Returns:
            str: Path del file audio convertito
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File video non trovato: {video_path}")
        
        # Genera path di output se non fornito
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            # Pulisce il nome del file da caratteri problematici
            base_name = re.sub(r'[^\w\s-]', '', base_name).strip()
            output_path = os.path.join(self.temp_dir, f"{base_name}.{audio_format}")
        
        # Mappa formati a codec ffmpeg
        format_codec_map = {
            'mp3': ('libmp3lame', 'mp3'),
            'wav': ('pcm_s16le', 'wav'),
            'flac': ('flac', 'flac'),
            'ogg': ('libvorbis', 'ogg'),
            'm4a': ('aac', 'm4a'),
            'opus': ('libopus', 'opus')
        }
        
        if audio_format not in format_codec_map:
            raise ValueError(f"Formato audio non supportato: {audio_format}")
        
        codec, container = format_codec_map[audio_format]
        
        # Comando ffmpeg per conversione
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # Nessun video
            '-acodec', codec,
            '-y',  # Sovrascrive file esistenti
            output_path
        ]
        
        # Opzioni specifiche per formato
        if audio_format == 'mp3':
            cmd.insert(-1, '-q:a')
            cmd.insert(-1, '0')  # Qualità massima
        elif audio_format == 'wav':
            cmd.insert(-1, '-ar')
            cmd.insert(-1, '44100')  # Sample rate
            cmd.insert(-1, '-ac')
            cmd.insert(-1, '2')  # Stereo
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            if not os.path.exists(output_path):
                raise FileNotFoundError("File audio non creato dopo la conversione")
            
            return output_path
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            raise Exception(f"Errore durante la conversione con ffmpeg: {error_msg}")
    
    def analyze_audio(self, audio_path):
        """
        Analizza l'audio per rilevare BPM e scala musicale
        
        Args:
            audio_path: Path del file audio da analizzare
        
        Returns:
            tuple: (bpm, scale) dove bpm è un int e scale è una stringa
        """
        try:
            print(f"Analyzing audio for BPM and key detection...")
            
            # Carica l'audio (usa solo i primi 30 secondi per velocità)
            y, sr = librosa.load(audio_path, duration=30.0)
            
            # Rileva BPM
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            # tempo può essere un array, prendi il primo valore o la media
            if isinstance(tempo, np.ndarray):
                tempo = float(tempo[0]) if len(tempo) > 0 else float(np.mean(tempo))
            bpm = int(round(float(tempo)))
            
            # Rileva la tonalità/scala
            # Usa chroma features per determinare la tonalità
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Nomi delle note
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Trova la nota principale (quella con il valore più alto)
            main_note_idx = np.argmax(chroma_mean)
            main_note = note_names[main_note_idx]
            
            # Determina se è maggiore o minore
            # Confronta le energie delle terze maggiori e minori
            # Per semplicità, usiamo un'euristica basata sulla distribuzione cromatica
            # Se la terza maggiore (4 semitoni) ha più energia, è maggiore
            third_major_idx = (main_note_idx + 4) % 12
            third_minor_idx = (main_note_idx + 3) % 12
            
            third_major_energy = chroma_mean[third_major_idx]
            third_minor_energy = chroma_mean[third_minor_idx]
            
            if third_major_energy > third_minor_energy:
                scale_type = "Major"
            else:
                scale_type = "Minor"
            
            scale = f"{main_note} {scale_type}"
            
            print(f"BPM detected: {bpm}, Key detected: {scale}")
            
            return bpm, scale
        
        except Exception as e:
            print(f"Error during audio analysis: {e}")
            # On error, return default values
            return None, None
    
    def sanitize_filename(self, filename):
        """Rimuove caratteri non validi dal nome del file"""
        # Rimuove caratteri problematici
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Sostituisce spazi multipli con uno solo
        filename = re.sub(r'\s+', ' ', filename)
        # Rimuove spazi agli estremi
        filename = filename.strip()
        return filename
    
    def generate_filename(self, title, bpm=None, scale=None, audio_format='mp3'):
        """
        Genera il nome del file nel formato: Track-BPM-Scale.ext
        Esempio: Track1-130BPM-AMinor.mp3
        
        Args:
            title: Titolo del video
            bpm: BPM (opzionale)
            scale: Scala musicale (opzionale)
            audio_format: Formato audio
        
        Returns:
            str: Nome del file formattato
        """
        # Pulisce il titolo e rimuove caratteri speciali
        track_name = self.sanitize_filename(title)
        # Rimuove caratteri speciali eccessivi, mantiene solo lettere, numeri, spazi e trattini
        track_name = re.sub(r'[^\w\s-]', '', track_name)
        # Sostituisce spazi multipli con uno solo
        track_name = re.sub(r'\s+', ' ', track_name).strip()
        # Sostituisce spazi con trattini per compatibilità
        track_name = track_name.replace(' ', '-')
        # Limita la lunghezza
        if len(track_name) > 50:
            track_name = track_name[:50]
        # Rimuove trattini multipli
        track_name = re.sub(r'-+', '-', track_name).strip('-')
        
        # Se il nome è vuoto, usa un default
        if not track_name:
            track_name = "Track"
        
        # Costruisce il nome del file
        parts = [track_name]
        
        if bpm:
            # Assicura che BPM sia un numero valido
            try:
                bpm_int = int(float(bpm))
                if bpm_int > 0 and bpm_int <= 300:  # Range ragionevole per BPM
                    parts.append(f"{bpm_int}BPM")
            except (ValueError, TypeError):
                pass
        
        if scale:
            # Pulisce la scala e rimuove spazi
            scale_clean = self.sanitize_filename(scale)
            scale_clean = re.sub(r'[^\w\s-]', '', scale_clean)
            # Rimuove spazi e unisce (es: "A Minor" -> "AMinor")
            scale_clean = scale_clean.replace(' ', '')
            if scale_clean and len(scale_clean) <= 20:  # Limita lunghezza
                parts.append(scale_clean)
        
        # Unisce le parti con trattini
        # Se non ci sono BPM o scala, usa solo il titolo
        if len(parts) == 1:
            filename = track_name
        else:
            filename = '-'.join(parts)
        
        # Aggiunge estensione
        return f"{filename}.{audio_format}"
    
    def convert(self, youtube_url, audio_format='mp3'):
        """
        Metodo principale: scarica video YouTube e converte in audio
        
        Args:
            youtube_url: URL del video YouTube
            audio_format: Formato audio desiderato
        
        Returns:
            str: Path del file audio convertito
        """
        video_path = None
        audio_path = None
        video_info = None
        temp_audio_path = None
        
        try:
            # Download video
            print(f"Download video da: {youtube_url}")
            video_path, video_info = self.download_video(youtube_url)
            
            # Estrae il titolo
            title = video_info.get('title', 'Track')
            
            # Conversione in audio (prima in un file temporaneo)
            print(f"Conversione in formato {audio_format}...")
            temp_audio_path = self.convert_to_audio(video_path, audio_format)
            
            # Analizza l'audio per rilevare BPM e scala
            bpm, scale = self.analyze_audio(temp_audio_path)
            
            # Genera il nome del file con BPM e scala rilevati
            custom_filename = self.generate_filename(title, bpm, scale, audio_format)
            final_output_path = os.path.join(self.temp_dir, custom_filename)
            
            # Rinomina il file con il nome corretto
            if os.path.exists(temp_audio_path):
                if os.path.exists(final_output_path):
                    os.remove(final_output_path)
                os.rename(temp_audio_path, final_output_path)
                audio_path = final_output_path
            else:
                audio_path = temp_audio_path
            
            # Pulisce file video temporaneo
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception as e:
                    print(f"Avviso: impossibile rimuovere file temporaneo {video_path}: {e}")
            
            return audio_path
        
        except Exception as e:
            # Pulizia in caso di errore
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
            if audio_path and os.path.exists(audio_path) and audio_path != temp_audio_path:
                try:
                    os.remove(audio_path)
                except:
                    pass
            raise

