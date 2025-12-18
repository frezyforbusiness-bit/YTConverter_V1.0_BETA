# YouTube Audio Converter

Applicazione web per convertire video YouTube in file audio in vari formati (MP3, WAV, FLAC, OGG, M4A, Opus).

## Caratteristiche

- 🎵 Conversione video YouTube in audio
- 📦 Supporto per 6 formati audio: MP3, WAV, FLAC, OGG, M4A, Opus
- 🌐 Interfaccia web moderna e responsive
- ⚡ API REST con Flask
- 🔄 Gestione automatica dei file temporanei

## Requisiti

Prima di iniziare, assicurati di avere installato:

- **Python 3.8+**
- **ffmpeg** - Necessario per la conversione audio

### Installazione ffmpeg

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (WSL2)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
Scarica da [ffmpeg.org](https://ffmpeg.org/download.html) o usa:
```bash
choco install ffmpeg
```

Verifica l'installazione:
```bash
ffmpeg -version
```

## Installazione

1. **Clona o naviga nella directory del progetto**
```bash
cd audioConverter
```

2. **Crea un ambiente virtuale Python (consigliato)**
```bash
python3 -m venv venv
source venv/bin/activate  # Su Linux/macOS
# oppure
venv\Scripts\activate  # Su Windows
```

3. **Installa le dipendenze**
```bash
cd backend
pip install -r requirements.txt
```

## Utilizzo

### Avvio del Backend

1. **Attiva l'ambiente virtuale** (se non già attivo)
```bash
source venv/bin/activate  # Linux/macOS
# oppure
venv\Scripts\activate  # Windows
```

2. **Avvia il server Flask**
```bash
cd backend
python app.py
```

Il server sarà disponibile su `http://localhost:5000`

### Utilizzo del Frontend

1. **Apri il file frontend**
   - Apri `frontend/index.html` nel tuo browser
   - Oppure usa un server HTTP locale:
     ```bash
     cd frontend
     python3 -m http.server 8000
     ```
     Poi apri `http://localhost:8000` nel browser

2. **Converti un video**
   - Incolla il link YouTube nel campo di input
   - Seleziona il formato audio desiderato
   - Clicca su "Converti"
   - Il file audio verrà scaricato automaticamente

## Struttura del Progetto

```
audioConverter/
├── backend/
│   ├── app.py              # Server Flask principale
│   ├── converter.py        # Logica di conversione
│   └── requirements.txt    # Dipendenze Python
├── frontend/
│   ├── index.html          # Interfaccia utente
│   ├── style.css           # Stili CSS
│   └── script.js           # Logica frontend
├── README.md               # Questa documentazione
└── .gitignore              # File da escludere da git
```

## API Endpoints

### `POST /convert`
Converte un video YouTube in file audio.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "format": "mp3"
}
```

**Response:**
- Successo: File audio (binary)
- Errore: JSON con messaggio di errore

**Formati supportati:** `mp3`, `wav`, `flac`, `ogg`, `m4a`, `opus`

### `GET /health`
Verifica lo stato del server.

**Response:**
```json
{
  "status": "ok"
}
```

## Risoluzione Problemi

### Errore: "ffmpeg non trovato"
- Assicurati che ffmpeg sia installato e disponibile nel PATH
- Verifica con `ffmpeg -version`

### Errore: "URL YouTube non valido"
- Controlla che l'URL sia completo e valido
- Formato supportato: `https://www.youtube.com/watch?v=...`

### Errore: "Impossibile connettersi al server"
- Verifica che il backend sia avviato su `http://localhost:5000`
- Controlla che non ci siano errori nella console del server

### Video non disponibile
- Alcuni video potrebbero essere protetti o non disponibili nella tua regione
- Prova con un altro video

## Note Legali

Questo strumento è fornito solo a scopo educativo. Assicurati di rispettare i termini di servizio di YouTube e le leggi sul copyright quando utilizzi questo strumento. Non utilizzare per scaricare contenuti protetti da copyright senza autorizzazione.

## Licenza

Questo progetto è fornito "così com'è" senza garanzie di alcun tipo.

