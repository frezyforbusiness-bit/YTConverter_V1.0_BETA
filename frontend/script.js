const API_URL = 'http://localhost:5000';

const form = document.getElementById('converterForm');
const convertBtn = document.getElementById('convertBtn');
const btnText = convertBtn.querySelector('.btn-text');
const btnLoader = convertBtn.querySelector('.btn-loader');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressMessage = document.getElementById('progressMessage');
const progressPercent = document.getElementById('progressPercent');

// Nasconde i messaggi
function hideMessages() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
}

// Mostra/nasconde progress bar
function showProgress(percent, message) {
    progressContainer.style.display = 'block';
    updateProgress(percent, message);
}

function hideProgress() {
    progressContainer.style.display = 'none';
    progressBar.style.width = '0%';
}

function updateProgress(percent, message) {
    const clampedPercent = Math.max(0, Math.min(100, percent));
    progressBar.style.width = `${clampedPercent}%`;
    progressPercent.textContent = `${Math.round(clampedPercent)}%`;
    progressMessage.textContent = message;
}

// Mostra messaggio di errore (informale)
function showError(message) {
    // Aggiunge un prefisso informale se non c'è già un emoji
    if (!message.match(/^[😬😅🤦🙄❌⚠️]/)) {
        errorMessage.textContent = `😬 Ops! ${message}`;
    } else {
        errorMessage.textContent = message;
    }
    errorMessage.style.display = 'flex';
    successMessage.style.display = 'none';
}

// Mostra messaggio di successo (informale)
function showSuccess(message) {
    // Aggiunge un prefisso informale se non c'è già un emoji
    if (!message.match(/^[🎉✅👍✨]/)) {
        successMessage.textContent = `🎉 ${message}`;
    } else {
        successMessage.textContent = message;
    }
    successMessage.style.display = 'flex';
    errorMessage.style.display = 'none';
}

// Valida URL YouTube
function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/.+/;
    return youtubeRegex.test(url);
}

// Gestisce lo stato di caricamento del bottone
function setLoading(loading) {
    if (loading) {
        convertBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
    } else {
        convertBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Gestisce il download del file
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Gestisce l'invio del form
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    hideMessages();
    
    const youtubeUrl = document.getElementById('youtubeUrl').value.trim();
    const audioFormat = document.getElementById('audioFormat').value;
    
    // Validazione URL
    if (!youtubeUrl) {
        showError('Dai, metti un link YouTube! 😅');
        return;
    }
    
    if (!isValidYouTubeUrl(youtubeUrl)) {
        showError('Questo non sembra un link YouTube valido... 🤔');
        return;
    }
    
    // Verifica se è una playlist (non supportata)
    // Rifiuta URL esplicitamente di playlist, ma permette video singoli anche se hanno parametro list=
    if (youtubeUrl.includes('/playlist')) {
        showError('Le playlist? Non ancora, scusa! Usa un video singolo 🙄');
        return;
    }
    
    setLoading(true);
    hideMessages();
    showProgress(0, 'Ok, partiamo! 🚀');
    
    let pollInterval = null;
    
    try {
        // Invia richiesta al backend per avviare la conversione
        const response = await fetch(`${API_URL}/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: youtubeUrl,
                format: audioFormat
            })
        });
        
        if (!response.ok) {
            let errorMsg = 'Errore durante la conversione';
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch (e) {
                errorMsg = `Errore ${response.status}: ${response.statusText}`;
            }
            showError(errorMsg);
            setLoading(false);
            hideProgress();
            return;
        }
        
        const data = await response.json();
        const taskId = data.task_id;
        
        if (!taskId) {
            showError('Qualcosa è andato storto, riprova! 🤦');
            setLoading(false);
            hideProgress();
            return;
        }
        
        // Inizia il polling per lo stato
        pollInterval = setInterval(async () => {
            try {
                const statusResponse = await fetch(`${API_URL}/status/${taskId}`);
                
                if (!statusResponse.ok) {
                    clearInterval(pollInterval);
                    showError('Ops, problema di comunicazione con il server 😬');
                    setLoading(false);
                    hideProgress();
                    return;
                }
                
                const status = await statusResponse.json();
                
                // Aggiorna progress bar e messaggio
                updateProgress(status.progress, status.message);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    
                    // Scarica il file
                    try {
                        const downloadResponse = await fetch(`${API_URL}/download/${taskId}`);
                        
                        if (!downloadResponse.ok) {
                            throw new Error('Problema nel download, riprova!');
                        }
                        
                        const blob = await downloadResponse.blob();
                        const filename = status.file ? status.file.split('/').pop() : `audio.${audioFormat}`;
                        
                        downloadFile(blob, filename);
                        
                        showSuccess(`Fatto! Il tuo file ${audioFormat.toUpperCase()} è pronto! 🎵`);
                        setLoading(false);
                        
                        // Reset form dopo 3 secondi
                        setTimeout(() => {
                            form.reset();
                            hideMessages();
                            hideProgress();
                        }, 3000);
                        
                    } catch (error) {
                        console.error('Errore nel download:', error);
                        showError(`Download fallito: ${error.message} 😅`);
                        setLoading(false);
                        hideProgress();
                    }
                    
                } else if (status.status === 'error') {
                    clearInterval(pollInterval);
                    const errorMsg = status.error || 'Qualcosa è andato storto durante la conversione';
                    showError(errorMsg.includes('playlist') ? 'Niente playlist, solo video singoli! 🙄' : `😬 ${errorMsg}`);
                    setLoading(false);
                    hideProgress();
                }
                
            } catch (error) {
                console.error('Errore nel polling:', error);
                clearInterval(pollInterval);
                showError('Il server non risponde, controlla che sia avviato! 🤷');
                setLoading(false);
                hideProgress();
            }
        }, 500); // Poll ogni 500ms
        
    } catch (error) {
        console.error('Errore:', error);
        
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('Il server non risponde! Assicurati che sia avviato su http://localhost:5000 🔌');
        } else {
            showError(`Ops! ${error.message} 😅`);
        }
        
        setLoading(false);
        hideProgress();
    }
});

// Verifica lo stato del server all'avvio (silenzioso, senza mostrare errori)
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            console.log('✅ Server connesso');
        }
    } catch (error) {
        console.warn('⚠️ Server non raggiungibile:', error);
        // Non mostriamo errore all'avvio, solo in console
    }
}

// Controlla lo stato del server quando la pagina carica
window.addEventListener('load', () => {
    checkServerStatus();
});

