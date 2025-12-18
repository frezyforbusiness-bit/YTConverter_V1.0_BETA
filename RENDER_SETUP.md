# Render Setup Guide - Step by Step

## Backend Setup (Web Service)

### Step 1: Create New Web Service
1. Vai su https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connetti il tuo repository GitHub
4. Seleziona il repository: `YTConverter_V1.0_BETA` (o il nome del tuo repo)

### Step 2: Basic Settings

**Name:**
```
producer-tools-backend
```

**Region:**
```
Oregon (US West)  (o quello più vicino a te)
```

**Branch:**
```
master  (o main, dipende dal tuo repo)
```

**Root Directory:**
```
(lasciare vuoto)
```

### Step 3: Environment Settings

**Environment:**
```
Docker  ⚠️ IMPORTANTE: Seleziona "Docker" NON "Python"!
```

**Dockerfile Path:**
```
Dockerfile
```
(oppure lascia vuoto se il Dockerfile è nella root)

**Docker Context:**
```
.
```
(oppure lascia vuoto)

### Step 4: Build & Deploy

**Build Command:**
```
(lasciare vuoto - Docker usa il Dockerfile)
```

**Start Command:**
```
(lasciare vuoto - Docker usa il CMD del Dockerfile)
```

### Step 5: Plan

**Plan:**
```
Free  (per iniziare, poi puoi upgradare)
```

### Step 6: Environment Variables (OPZIONALE)

Non sono necessari per il funzionamento base, ma puoi aggiungere:

- `PORT`: `5000` (Render lo imposta automaticamente, ma puoi specificarlo)
- `FLASK_ENV`: `production` (per disabilitare debug mode)

#### ⚠️ IMPORTANTE: Configurazione Cookies per YouTube

Per evitare errori "Sign in to confirm you're not a bot" da YouTube:

**⚠️ NOTA**: Se ricevi l'errore `argument list too long`, usa il **Metodo 2 (SSH)** invece del Metodo 1.

##### Metodo 1: Variabile d'Ambiente (solo per cookies piccoli < 100KB)

1. **Converti il file cookies.txt in base64:**
   ```bash
   cd backend
   python encode_cookies.py
   ```

2. **Copia l'output base64** (la stringa lunga tra le linee ===)

3. **In Render Dashboard:**
   - Vai su **Environment** (nel menu laterale del tuo servizio)
   - Click **"Add Environment Variable"**
   - **Key**: `COOKIES_BASE64`
   - **Value**: (incolla la stringa base64 copiata prima)
   - Click **"Save Changes"**

4. **Riavvia il servizio** (Render lo farà automaticamente dopo aver salvato)

**⚠️ Se ricevi "argument list too long"**, il file è troppo grande. Usa il Metodo 2.

##### Metodo 1: Render Secret Files (IL PIÙ SEMPLICE) ⭐

**Metodo ufficiale di Render - il più semplice!**

1. **Vai su Render Dashboard:**
   - Il tuo servizio → **Environment**
   - Scorri fino a **"Secret Files"**
   - Click **"+ Add Secret File"**

2. **Configura:**
   - **File Name**: `cookies.txt`
   - **Contents**: (incolla tutto il contenuto del tuo `cookies.txt` locale)

3. **Salva** → Render riavvierà automaticamente

Il file sarà disponibile in `/etc/secrets/cookies.txt` e il codice lo troverà automaticamente!

##### Metodo 2: Upload via API (Alternativa) 🚀

**Il metodo più semplice! Carica il file dalla tua macchina usando curl.**

1. **Configura un token su Render:**
   - Environment → Aggiungi `UPLOAD_TOKEN` (es: `my-secret-123`)

2. **Carica il file dalla tua macchina:**
   ```bash
   curl -X POST https://your-render-url.onrender.com/admin/upload-cookies \
        -H "Authorization: Bearer my-secret-123" \
        -F "file=@backend/cookies.txt"
   ```

3. **Fatto!** Il file verrà salvato automaticamente.

Vedi `RENDER_COOKIES_SETUP.md` per istruzioni dettagliate e metodi alternativi.

##### Metodo 3: Upload via Render Shell (Alternativa)

Se preferisci usare la Shell web di Render:
1. Dashboard → Il tuo servizio → **Shell**
2. `mkdir -p /app/backend && cd /app/backend`
3. `nano cookies.txt` (incolla il contenuto)
4. Riavvia il servizio

Il file cookies.txt verrà trovato automaticamente all'avvio del server!

### Step 7: Deploy

Click **"Create Web Service"**

Render inizierà il build. Dovrebbe:
1. Buildare l'immagine Docker
2. Installare FFmpeg
3. Installare le dipendenze Python
4. Avviare il server

---

## Frontend Setup (Static Site)

### Step 1: Create New Static Site
1. Vai su https://dashboard.render.com
2. Click **"New +"** → **"Static Site"**
3. Connetti il tuo repository GitHub
4. Seleziona lo stesso repository

### Step 2: Basic Settings

**Name:**
```
producer-tools-frontend
```

**Branch:**
```
master  (o main)
```

**Root Directory:**
```
(lasciare vuoto)
```

### Step 3: Build Settings

**Build Command:**
```
(lasciare completamente vuoto)
```

**Publish Directory:**
```
frontend
```

### Step 4: Plan

**Plan:**
```
Free
```

### Step 5: Environment Variables

**NON necessari** per il frontend

### Step 6: Deploy

Click **"Create Static Site"**

---

## Dopo il Deploy

### 1. Ottieni l'URL del Backend
- Vai al tuo Web Service (backend)
- Copia l'URL (es: `https://producer-tools-backend.onrender.com`)

### 2. Aggiorna il Frontend (se necessario)

Il frontend dovrebbe auto-rilevare l'URL, ma se backend e frontend sono su domini diversi:

1. Vai al tuo Static Site (frontend)
2. Click **"Manual Deploy"** → **"Clear build cache & deploy"**
3. Oppure modifica `frontend/script.js` e hardcode l'URL:

```javascript
const API_URL = 'https://producer-tools-backend.onrender.com';
```

### 3. Test

1. Vai all'URL del frontend
2. Prova a convertire un video YouTube
3. Controlla i logs del backend se ci sono errori

---

## Troubleshooting

### Backend non si avvia
- Controlla i logs in Render Dashboard
- Verifica che il Dockerfile sia corretto
- Assicurati che `backend/app.py` esista

### FFmpeg non trovato
- Se usi Docker, FFmpeg è incluso automaticamente
- Se usi Python environment, devi installarlo manualmente (difficile su free tier)

### Frontend non si connette al backend
- Verifica che l'URL del backend sia corretto
- Controlla CORS settings nel backend
- Assicurati che entrambi i servizi siano deployed

### Build fallisce
- Controlla i logs di build
- Verifica che `backend/requirements.txt` esista
- Assicurati che il Dockerfile sia nella root del repo

---

## Riepilogo Impostazioni Backend

```
Name: producer-tools-backend
Environment: Docker
Dockerfile Path: Dockerfile
Docker Context: .
Build Command: (vuoto)
Start Command: (vuoto)
Plan: Free
```

## Riepilogo Impostazioni Frontend

```
Name: producer-tools-frontend
Build Command: (vuoto)
Publish Directory: frontend
Plan: Free
```


