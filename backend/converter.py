import os
import subprocess
import yt_dlp
import tempfile
from pathlib import Path
import re
import librosa
import numpy as np
import uuid
import base64


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
        
        # Path del file cookies - controlla in ordine di priorità:
        # 1. Variabile d'ambiente COOKIES_FILE (custom path)
        # 2. Render Secret Files (copiati in directory scrivibile)
        # 3. Path di default (backend/cookies.txt)
        cookies_file_env = os.environ.get('COOKIES_FILE')
        if cookies_file_env:
            self.cookies_path = cookies_file_env
        else:
            # Path di default (relativo alla directory backend) - scrivibile
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            self.cookies_path = os.path.join(backend_dir, 'cookies.txt')
        
        # Crea il file cookies da variabile d'ambiente se presente (per Render/produzione)
        self._create_cookies_from_env()
        
        # Copia Render Secret Files in directory scrivibile (se presente)
        # I Secret Files sono read-only, quindi devono essere copiati
        self._copy_render_secret_file()
        
        # Verifica se il file cookies esiste e informa
        if os.path.exists(self.cookies_path):
            file_size = os.path.getsize(self.cookies_path)
            print(f"✓ Cookies file found: {self.cookies_path} ({file_size} bytes)")
        else:
            print(f"⚠ Cookies file not found at: {self.cookies_path}")
            print(f"   YouTube downloads may fail with bot detection errors.")
    
    def ensure_temp_dir(self):
        """Assicura che la directory temporanea esista"""
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _create_cookies_from_env(self):
        """
        Crea il file cookies.txt da variabile d'ambiente COOKIES_BASE64 se presente.
        Utile per deployment su Render/Railway dove non si può committare il file.
        
        NOTA: Se COOKIES_BASE64 è troppo lungo (causa "argument list too long" su Render),
        carica invece il file cookies.txt direttamente via SSH dopo il deploy.
        """
        cookies_base64 = os.environ.get('COOKIES_BASE64')
        if cookies_base64:
            # Limite di sicurezza: se troppo lungo, potrebbe causare problemi
            # Render ha un limite di ~128KB per le env vars, ma il processo di build
            # può avere limiti più stringenti
            if len(cookies_base64) > 100000:  # ~100KB
                print(f"⚠ Warning: COOKIES_BASE64 is very long ({len(cookies_base64)} chars)")
                print(f"   This may cause 'argument list too long' errors on Render.")
                print(f"   Consider uploading cookies.txt directly via SSH instead.")
                print(f"   See documentation for alternative methods.")
                # Non proviamo nemmeno a creare il file se è troppo lungo
                return
            
            try:
                # Decodifica il contenuto base64
                cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
                # Crea il file cookies.txt
                with open(self.cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
                print(f"✓ Cookies file created from COOKIES_BASE64 environment variable")
            except Exception as e:
                print(f"⚠ Warning: Failed to create cookies file from COOKIES_BASE64: {e}")
                # Non blocca l'avvio se fallisce
    
    def _copy_render_secret_file(self):
        """
        Copia il file cookies.txt da Render Secret Files in una directory scrivibile.
        I Secret Files sono read-only (/etc/secrets/), quindi devono essere copiati
        per essere usati da yt-dlp.
        
        Render Secret Files sono accessibili da:
        - /etc/secrets/cookies.txt (path standard)
        - /app/cookies.txt (root dell'app)
        - cookies.txt (root relativa)
        """
        # Render Secret Files sono accessibili da /etc/secrets/ o dalla root dell'app
        secret_paths = [
            '/etc/secrets/cookies.txt',  # Path standard Render
            '/app/cookies.txt',  # Root dell'app (Render Docker)
            'cookies.txt'  # Root relativa
        ]
        
        for secret_path in secret_paths:
            if os.path.exists(secret_path):
                try:
                    # Leggi il contenuto dal Secret File (read-only)
                    with open(secret_path, 'r', encoding='utf-8') as f:
                        cookies_content = f.read()
                    
                    # Scrivi in una directory scrivibile (backend/cookies.txt)
                    with open(self.cookies_path, 'w', encoding='utf-8') as f:
                        f.write(cookies_content)
                    
                    print(f"✓ Copied Render Secret File from {secret_path} to {self.cookies_path}")
                    return
                except Exception as e:
                    print(f"⚠ Warning: Failed to copy Render Secret File from {secret_path}: {e}")
                    # Prova il prossimo path
                    continue
    
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
        
        # Lista di client da provare in ordine (fallback se uno fallisce)
        # Ogni client ha caratteristiche diverse e alcuni funzionano meglio con cookies
        player_clients = ['ios', 'android', 'web', 'mweb']
        
        # Prova ogni client finché uno non funziona
        last_error = None
        for client in player_clients:
            try:
                print(f"Trying YouTube client: {client}...")
                
                # Optimized yt-dlp configuration for cloud environments (Render, Docker, VPS)
                # Force IPv4 - important for Render (often prefers IPv6 which breaks YouTube)
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'quiet': False,  # Mostra warnings per debug
                    'no_warnings': False,
                    'cachedir': False,
                    'force_ipv4': True,  # Force IPv4 - critical for Render
                    'retries': 3,
                    'socket_timeout': 30,
                    'extractor_args': {
                        'youtube': {
                            'player_client': [client],
                        }
                    }
                }
                
                # Aggiungi cookies se il file esiste
                if os.path.exists(self.cookies_path):
                    ydl_opts['cookiefile'] = self.cookies_path
                    print(f"Using cookies file: {self.cookies_path}")
                else:
                    print(f"Cookies file not found at {self.cookies_path}, proceeding without cookies")
                
                # Extract info first (validates URL and checks for playlists)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
                
                # Check if audio formats are available
                formats = info.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if not audio_formats and not get_info_only:
                    # Se non ci sono formati audio puri, continua comunque (bestaudio/best prenderà il migliore)
                    print(f"⚠ Warning: No pure audio formats found, will use best available format")
                
                # If only info is needed, return now
                if get_info_only:
                    return None, info
                
                # Download the video
                print(f"Downloading with {client} client...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
                print(f"✓ Successfully downloaded video using {client} client")
                return video_path, info
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠ Client {client} failed: {error_msg[:200]}")
                last_error = e
                # Continue to next client
                continue
        
        # Se tutti i client hanno fallito, solleva l'ultimo errore
        if last_error:
            error_msg = str(last_error)
            print(f"All clients failed. Last error: {error_msg[:200]}...")
            
            # Don't retry on playlist errors (user error)
            if 'playlist' in error_msg.lower():
                raise ValueError("Playlists are not supported. Use a single video URL.")
            
            # Raise error with clear message
            self._raise_download_error(error_msg)
    
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

