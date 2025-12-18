#!/bin/bash

# Script di avvio per YouTube Audio Converter

echo "🎵 YouTube Audio Converter - Setup e Avvio"
echo "=========================================="
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installa Python 3.8 o superiore."
    exit 1
fi

echo "✓ Python trovato: $(python3 --version)"

# Verifica ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "⚠️  ffmpeg non trovato!"
    echo "Installa ffmpeg con: sudo apt install ffmpeg"
    echo "Poi riprova questo script."
    exit 1
fi

echo "✓ ffmpeg trovato: $(ffmpeg -version | head -n 1)"

# Crea virtual environment se non esiste o se è corrotto
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo ""
    echo "📦 Creazione ambiente virtuale..."
    # Rimuovi venv esistente se corrotto
    if [ -d "venv" ]; then
        rm -rf venv
    fi
    python3 -m venv venv || {
        echo "❌ Errore nella creazione del virtual environment."
        echo "Installa python3-venv con: sudo apt install python3-venv"
        exit 1
    }
    
    # Verifica che il venv sia stato creato correttamente
    if [ ! -f "venv/bin/activate" ]; then
        echo "❌ Errore: virtual environment non creato correttamente."
        exit 1
    fi
fi

# Attiva virtual environment
echo ""
echo "🔧 Attivazione ambiente virtuale..."
source venv/bin/activate || {
    echo "❌ Errore nell'attivazione del virtual environment."
    exit 1
}

# Verifica che pip sia disponibile
if ! command -v pip &> /dev/null; then
    echo "❌ pip non trovato nel virtual environment."
    echo "Rimuovi il venv e ricrea: rm -rf venv"
    exit 1
fi

# Installa dipendenze
echo ""
echo "📥 Installazione dipendenze..."
cd backend
pip install --upgrade pip --quiet
pip install -r requirements.txt

# Torna alla root
cd ..

echo ""
echo "✅ Setup completato!"
echo ""
echo "🚀 Avvio del server..."
echo "Il server sarà disponibile su: http://localhost:5000"
echo "Apri frontend/index.html nel browser per utilizzare l'applicazione"
echo ""
echo "Premi Ctrl+C per fermare il server"
echo ""

# Avvia il server
cd backend
python3 app.py

