# Guida Rapida - Come Provare l'Applicazione

## Passo 1: Installa i Prerequisiti

### Installa ffmpeg
```bash
sudo apt update
sudo apt install ffmpeg
```

### Installa python3-venv (se necessario)
```bash
sudo apt install python3-venv
```

Verifica che tutto sia installato:
```bash
ffmpeg -version
python3 --version
```

## Passo 2: Avvia l'Applicazione

### Opzione A: Usa lo script di avvio (consigliato)
```bash
cd /home/fpiumatti/myProjects/audioConverter
./start.sh
```

### Opzione B: Avvio manuale

1. **Crea e attiva l'ambiente virtuale:**
```bash
cd /home/fpiumatti/myProjects/audioConverter
python3 -m venv venv
source venv/bin/activate
```

2. **Installa le dipendenze:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Avvia il server:**
```bash
python app.py
```

Dovresti vedere:
```
Server avviato su http://localhost:5000
```

## Passo 3: Apri il Frontend

### Opzione A: Apri direttamente il file HTML
```bash
# Da un altro terminale
cd /home/fpiumatti/myProjects/audioConverter/frontend
# Apri index.html con il tuo browser preferito
# Su WSL2, puoi usare:
explorer.exe index.html
# oppure
xdg-open index.html
```

### Opzione B: Usa un server HTTP locale
```bash
# Da un altro terminale
cd /home/fpiumatti/myProjects/audioConverter/frontend
python3 -m http.server 8000
```
Poi apri nel browser: `http://localhost:8000`

## Passo 4: Prova la Conversione

1. **Apri l'interfaccia web** (index.html o http://localhost:8000)

2. **Incolla un link YouTube**, ad esempio:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

3. **Seleziona un formato audio** (MP3, WAV, FLAC, ecc.)

4. **Clicca su "Converti"**

5. **Attendi il download** - il file audio verrà scaricato automaticamente!

## Risoluzione Problemi

### Errore: "ffmpeg non trovato"
```bash
sudo apt install ffmpeg
```

### Errore: "python3-venv non disponibile"
```bash
sudo apt install python3-venv
```

### Errore: "Impossibile connettersi al server"
- Verifica che il backend sia avviato (dovresti vedere "Server avviato su http://localhost:5000")
- Controlla che non ci siano errori nella console del server

### Il browser non si connette
- Assicurati che il server Flask sia in esecuzione
- Verifica che l'URL nel browser sia corretto
- Se usi WSL2, potresti dover usare `http://localhost:5000` invece di `http://127.0.0.1:5000`

## Test Rapido via Terminale

Puoi anche testare l'API direttamente via curl:

```bash
curl -X POST http://localhost:5000/convert \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp3"}' \
  --output test_audio.mp3
```

Questo scaricherà il file audio come `test_audio.mp3` nella directory corrente.


