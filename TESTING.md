# Testing Guide - Render Deployment

## Step 1: Ottieni gli URL

### Backend (Web Service)
1. Vai su https://dashboard.render.com
2. Click sul tuo **Web Service** (es: `producer-tools-backend`)
3. Copia l'URL che vedi in alto (es: `https://producer-tools-backend.onrender.com`)

### Frontend (Static Site)
1. Vai su https://dashboard.render.com
2. Click sul tuo **Static Site** (es: `producer-tools-frontend`)
3. Copia l'URL che vedi in alto (es: `https://producer-tools-frontend.onrender.com`)

---

## Step 2: Test Backend

### Test 1: Health Check
Apri nel browser o usa curl:
```
https://your-backend-url.onrender.com/health
```

**Risposta attesa:**
```json
{"status": "ok"}
```

### Test 2: Root Endpoint
```
https://your-backend-url.onrender.com/
```

**Risposta attesa:**
```json
{"message": "Producer Tools - YouTube Audio Converter API"}
```

### Test 3: Verifica Logs
1. Vai al dashboard Render
2. Click sul tuo Web Service
3. Vai alla tab **"Logs"**
4. Dovresti vedere: `Server starting on http://0.0.0.0:5000`

---

## Step 3: Test Frontend

### Opzione A: Se Frontend e Backend sono sullo stesso dominio
Il frontend dovrebbe auto-rilevare l'URL del backend. Basta aprire:
```
https://your-frontend-url.onrender.com
```

### Opzione B: Se Frontend e Backend sono su domini diversi

1. **Apri il frontend:**
   ```
   https://your-frontend-url.onrender.com
   ```

2. **Aggiorna l'URL del backend nel codice:**
   - Vai su GitHub
   - Modifica `frontend/script.js`
   - Cambia la riga 1-3:
   ```javascript
   // Sostituisci con:
   const API_URL = 'https://your-backend-url.onrender.com';
   ```
   - Commit e push
   - Render farà auto-deploy

3. **Oppure usa la console del browser:**
   - Apri il frontend
   - Apri Developer Tools (F12)
   - Console → Esegui:
   ```javascript
   window.API_URL = 'https://your-backend-url.onrender.com';
   ```
   (Solo per test temporaneo)

---

## Step 4: Test Completo

1. **Apri il frontend** nel browser
2. **Incolla un URL YouTube** (es: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
3. **Seleziona un formato** (es: MP3)
4. **Click "Convert & Analyze"**
5. **Osserva:**
   - Progress bar che si riempie
   - Messaggi di stato che cambiano
   - File che viene scaricato automaticamente

---

## Step 5: Debugging

### Se il frontend non si connette al backend:

1. **Controlla CORS:**
   - Apri Developer Tools (F12)
   - Tab "Network"
   - Prova una conversione
   - Guarda se ci sono errori CORS (rosso)

2. **Verifica l'URL del backend:**
   - Console del browser (F12)
   - Esegui: `console.log(API_URL)`
   - Verifica che sia corretto

3. **Controlla i logs del backend:**
   - Render Dashboard → Web Service → Logs
   - Cerca errori o warning

### Se la conversione fallisce:

1. **Controlla i logs del backend:**
   - Render Dashboard → Web Service → Logs
   - Cerca messaggi di errore

2. **Verifica FFmpeg:**
   - Il backend dovrebbe avere FFmpeg installato (se usi Docker)
   - Controlla i logs per: `ERROR: ffmpeg not found`

3. **Test manuale del backend:**
   ```bash
   curl -X POST https://your-backend-url.onrender.com/convert \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp3"}'
   ```
   Dovresti ricevere un `task_id`

---

## Troubleshooting Comune

### "Server not responding"
- Verifica che il backend sia "Live" (non "Suspended")
- Render free tier sospende i servizi dopo inattività
- Il primo avvio può richiedere 30-60 secondi (cold start)

### "CORS error"
- Il backend ha CORS abilitato, ma verifica che l'URL sia corretto
- Se frontend e backend sono su domini diversi, potrebbe servire configurazione aggiuntiva

### "FFmpeg not found"
- Se usi Docker, FFmpeg è incluso
- Se usi Python environment, devi installarlo manualmente (difficile)

### "Task not found"
- Il task_id potrebbe essere scaduto
- I task vengono mantenuti in memoria, potrebbero essere persi al restart

---

## Quick Test Checklist

- [ ] Backend health check funziona (`/health`)
- [ ] Backend risponde al root (`/`)
- [ ] Frontend si carica correttamente
- [ ] Frontend può connettersi al backend (controlla Network tab)
- [ ] Conversione inizia (progress bar appare)
- [ ] File viene scaricato alla fine

---

## Note Importanti

1. **Cold Start**: Il primo request dopo inattività può richiedere 30-60 secondi
2. **Free Tier Limits**: 
   - Servizi possono essere sospesi dopo 15 minuti di inattività
   - File size limits possono applicarsi
3. **Timeout**: Conversioni lunghe potrebbero timeout su free tier
4. **Logs**: Controlla sempre i logs per debugging


