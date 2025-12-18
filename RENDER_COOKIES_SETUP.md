# Configurazione Cookies per Render - Guida Completa

## ⚠️ Problema: "argument list too long"

Se hai ricevuto l'errore `exec /usr/local/bin/run-buildkit.sh: argument list too long`, significa che la variabile d'ambiente `COOKIES_BASE64` è troppo lunga per Render.

## ✅ Soluzioni Disponibili

### Metodo 1: Upload via API (PIÙ SEMPLICE - CONSIGLIATO) 🚀

**Questo metodo ti permette di caricare il file dalla tua macchina usando curl!**

1. **Configura un token di sicurezza su Render:**
   - Vai su Render Dashboard → Il tuo servizio → **Environment**
   - Aggiungi variabile d'ambiente:
     - **Key**: `UPLOAD_TOKEN`
     - **Value**: (genera un token casuale, es: `my-secret-token-12345`)
     - Salva

2. **Carica il file dalla tua macchina:**
   ```bash
   curl -X POST https://your-render-url.onrender.com/admin/upload-cookies \
        -H "Authorization: Bearer my-secret-token-12345" \
        -F "file=@backend/cookies.txt"
   ```
   
   Sostituisci:
   - `https://your-render-url.onrender.com` con l'URL del tuo servizio Render
   - `my-secret-token-12345` con il token che hai impostato

3. **Verifica il successo:**
   Dovresti ricevere una risposta JSON:
   ```json
   {
     "success": true,
     "message": "Cookies file uploaded successfully",
     "path": "/app/backend/cookies.txt",
     "size": 386700
   }
   ```

4. **Riavvia il servizio** su Render (opzionale, ma consigliato)

**Vantaggi:**
- ✅ Funziona dalla tua macchina locale
- ✅ Non serve SSH
- ✅ Veloce e semplice
- ✅ Protetto da token

### Metodo 2: Upload via Render Shell (Alternativa)

1. **Dopo il deploy su Render**, vai su:
   - Dashboard → Il tuo servizio → **Shell** (o **SSH**)

2. **Crea la directory backend** (se non esiste):
   ```bash
   mkdir -p /app/backend
   cd /app/backend
   ```

3. **Carica il file cookies.txt**:
   - Opzione A: Usa `nano` o `vi` per creare il file:
     ```bash
     nano cookies.txt
     # Incolla il contenuto del tuo cookies.txt locale
     # Salva con Ctrl+X, poi Y, poi Enter
     ```
   
   - Opzione B: Usa `cat` con heredoc:
     ```bash
     cat > cookies.txt << 'EOF'
     # Incolla qui il contenuto del tuo cookies.txt
     # Termina con EOF su una nuova riga
     EOF
     ```

4. **Verifica che il file sia stato creato**:
   ```bash
   ls -lh cookies.txt
   ```

5. **Riavvia il servizio** su Render Dashboard

### Metodo 2: Usare Render's File System (se disponibile)

Alcuni piani Render permettono di caricare file direttamente. Controlla nella sezione "Files" del tuo servizio.

### Metodo 3: Script di Build Alternativo

Se preferisci automatizzare, puoi creare uno script che scarica i cookies da un URL privato:

1. **Carica cookies.txt su un servizio privato** (es. GitHub Gist privato, S3, ecc.)
2. **Aggiungi uno script di build** che scarica il file

## 🔧 Configurazione Alternativa: Variabile d'Ambiente Ridotta

Se vuoi comunque usare una variabile d'ambiente, puoi:

1. **Dividere i cookies in più variabili** (non consigliato, complesso)
2. **Usare solo i cookies essenziali** (riduce la dimensione ma può non funzionare)

## 📝 Verifica che i Cookies Funzionino

Dopo aver caricato il file, verifica nei log di Render che vedi:
```
✓ Cookies file found: /app/backend/cookies.txt
Using cookies file: /app/backend/cookies.txt
```

## 🚨 Troubleshooting

### Il file non viene trovato
- Verifica il percorso: dovrebbe essere `/app/backend/cookies.txt` (se usi Docker)
- Controlla i permessi: `chmod 644 cookies.txt`

### I cookies non funzionano
- Verifica che il file sia nel formato Netscape cookies
- Assicurati che i cookies non siano scaduti
- Controlla i log per errori di parsing

## 📚 Riferimenti

- [Render Shell Documentation](https://render.com/docs/shell)
- [yt-dlp Cookies Guide](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

