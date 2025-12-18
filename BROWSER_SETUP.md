# Browser Setup per Cookie Extraction

## Panoramica

L'applicazione estrae automaticamente i cookies di YouTube dai browser installati sul server per bypassare le restrizioni di YouTube. Questo documento spiega come installare e configurare i browser sul server.

## Browser Supportati

yt-dlp supporta l'estrazione automatica dei cookies da questi browser:
- **Firefox** (`firefox`)
- **Chrome** (`chrome`)
- **Chromium** (`chromium`)
- **Edge** (`edge`)
- **Opera** (`opera`)
- **Brave** (`brave`)
- **Vivaldi** (`vivaldi`)

## Installazione su Server Linux (Debian/Ubuntu)

### Opzione 1: Usando il Dockerfile (Raccomandato)

Il Dockerfile è già configurato per installare Chromium e Firefox. Quando usi Docker su Render, i browser vengono installati automaticamente.

### Opzione 2: Installazione Manuale su Server

#### Installare Chromium
```bash
sudo apt-get update
sudo apt-get install -y chromium chromium-driver
```

#### Installare Firefox
```bash
sudo apt-get update
sudo apt-get install -y firefox-esr
```

#### Creare Symlinks (per compatibilità)
```bash
# yt-dlp cerca 'chrome' o 'google-chrome', ma abbiamo solo 'chromium'
sudo ln -s /usr/bin/chromium /usr/bin/chrome
sudo ln -s /usr/bin/chromium /usr/bin/google-chrome
```

## Installazione su Render

### Usando Docker (Raccomandato)

1. **Assicurati di usare `render-docker.yaml`** invece di `render.yaml`
2. Il Dockerfile installa automaticamente:
   - Chromium
   - Firefox ESR
   - Driver necessari
3. Render userà il Dockerfile e installerà tutto automaticamente

### Configurazione Render

Nel dashboard Render:
1. Vai al tuo servizio backend
2. Assicurati che **Environment** sia impostato su **"Docker"**
3. **Dockerfile Path**: `Dockerfile`
4. Render installerà i browser durante il build

## Verifica Installazione

### Test Locale

Dopo aver buildato l'immagine Docker:
```bash
docker build -t audio-converter .
docker run -it audio-converter bash

# Dentro il container, verifica:
which chromium
which firefox
chromium --version
firefox --version
```

### Test su Render

Controlla i log di build su Render. Dovresti vedere:
```
Setting up chromium (xxx) ...
Setting up firefox-esr (xxx) ...
```

## Limitazioni

### ⚠️ Importante: Cookies sul Server

**I cookies vengono estratti dal browser installato sul SERVER, non dal browser dell'utente!**

Questo significa:
- Se l'utente è loggato su YouTube nel SUO browser, i cookies NON vengono usati
- I cookies devono essere presenti nel browser installato sul SERVER
- Su Render/server cloud, i browser sono "puliti" (nessun login)

### Soluzioni Alternative

1. **Usa un browser headless con login automatico** (complesso)
2. **Permetti all'utente di esportare cookies manualmente** (già rimosso)
3. **Usa un servizio proxy/API** (costo aggiuntivo)
4. **Accetta che alcuni video potrebbero fallire** (attuale comportamento)

## Troubleshooting

### Errore: "Browser not found"
- Verifica che il browser sia installato: `which chromium`
- Controlla i symlinks: `ls -la /usr/bin/chrome`

### Errore: "Cannot access browser cookies"
- I browser sul server non hanno cookies di YouTube
- Questo è normale su server cloud puliti
- L'estrazione fallirà ma yt-dlp proverà comunque

### Errore: "Permission denied"
- I browser potrebbero non avere permessi per accedere ai cookies
- Su server cloud, questo è spesso un problema di sicurezza

## Note per Produzione

1. **Su Render Free Plan**: I browser vengono installati ma potrebbero non avere accesso ai cookies utente
2. **Performance**: Chromium e Firefox aggiungono ~200-300MB all'immagine Docker
3. **Alternative**: Considera di usare un servizio esterno per i cookies se necessario

## Prossimi Passi

Se l'estrazione automatica non funziona su Render:
1. Verifica i log del backend per errori specifici
2. Considera di implementare un fallback (es. richiedere cookies manuali)
3. Valuta servizi esterni per gestire i cookies

