#!/usr/bin/env python3
"""
Script helper per convertire cookies.txt in base64 per Render.
Uso: python encode_cookies.py [path/to/cookies.txt]
"""

import sys
import base64
import os

def encode_cookies(cookies_path):
    """Converte il file cookies.txt in base64"""
    if not os.path.exists(cookies_path):
        print(f"❌ Errore: File non trovato: {cookies_path}")
        return None
    
    try:
        with open(cookies_path, 'rb') as f:
            cookies_content = f.read()
        
        # Codifica in base64
        cookies_base64 = base64.b64encode(cookies_content).decode('utf-8')
        
        # Salva anche in un file per facilitare la copia
        output_file = os.path.join(os.path.dirname(cookies_path), 'cookies_base64.txt')
        with open(output_file, 'w') as f:
            f.write(cookies_base64)
        
        print("✅ Cookies codificati in base64:")
        print(f"\n📄 Valore salvato anche in: {output_file}")
        print(f"📏 Lunghezza: {len(cookies_base64)} caratteri")
        print("\n" + "="*80)
        print("INIZIO DEL VALORE (primi 100 caratteri):")
        print(cookies_base64[:100])
        print("...")
        print("FINE DEL VALORE (ultimi 100 caratteri):")
        print(cookies_base64[-100:])
        print("="*80)
        print("\n📋 ISTRUZIONI PER RENDER:")
        print("   1. Apri il file cookies_base64.txt nella directory backend/")
        print("   2. Copia TUTTO il contenuto (Ctrl+A, Ctrl+C)")
        print("   3. Vai su Render Dashboard → Il tuo servizio → Environment")
        print("   4. Click 'Add Environment Variable'")
        print("   5. Key: COOKIES_BASE64")
        print("   6. Value: (incolla tutto il contenuto copiato)")
        print("   7. Save Changes")
        print(f"\n💡 Oppure usa: cat {output_file} | xclip (per copiare automaticamente)")
        
        return cookies_base64
    
    except Exception as e:
        print(f"❌ Errore durante la codifica: {e}")
        return None

if __name__ == '__main__':
    # Path di default
    default_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    
    if len(sys.argv) > 1:
        cookies_path = sys.argv[1]
    else:
        cookies_path = default_path
    
    encode_cookies(cookies_path)

