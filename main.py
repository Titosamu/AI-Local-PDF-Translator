import os
import shutil
import time
import subprocess
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 
import requests
import json
import re

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "ENTRADA_PDFS")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "SALIDA_TRADUCIDOS")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "PDFS_PROCESADOS")
ERROR_FOLDER = os.path.join(BASE_DIR, "PDFS_CON_ERROR")
TEMP_OCR_FOLDER = os.path.join(BASE_DIR, "TEMP_OCR") # Carpeta temporal para reparaciones

MODEL_NAME = "gemma2:9b"
API_URL = "http://localhost:11434/api/generate"
WORKERS = 4  # Bajamos a 2 porque el OCR consume mucha CPU

# --- FUNCIONES ---

def setup_folders():
    for f in [INPUT_FOLDER, OUTPUT_FOLDER, PROCESSED_FOLDER, ERROR_FOLDER, TEMP_OCR_FOLDER]:
        os.makedirs(f, exist_ok=True)

def reparar_pdf_ocr(input_path):
    """
    Ejecuta OCRmyPDF para arreglar la capa de texto corrupta (???? -> Texto Ruso Real)
    """
    filename = os.path.basename(input_path)
    output_path = os.path.join(TEMP_OCR_FOLDER, filename)
    
    # Si ya lo reparamos antes, no perder tiempo
    if os.path.exists(output_path):
        return output_path

    # Comando de reparación: Fuerza el idioma ruso y arregla el archivo
    cmd = [
        "ocrmypdf",
        "--language", "rus",
        "--force-ocr",      # Ignora el texto viejo roto y lee la imagen de nuevo
        "--deskew",         # Endereza si está torcido
        "--jobs", "2",      # Usa 2 núcleos
        "--output-type", "pdf",
        input_path,
        output_path
    ]
    
    try:
        # Ejecutamos OCR en silencio
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        return output_path
    except Exception:
        # Si falla el OCR, devolvemos el original y cruzamos los dedos
        return input_path

def translate_text(text, model):
    """
    Traducción Directa (Estilo Script 1) pero sin alucinaciones.
    """
    text = text.strip()
    if len(text) < 2 or text.isdigit(): return text

    # Prompt simple y directo, como el que te gustaba al principio
    prompt = (
        f"Translate this Russian text to Spanish. Output ONLY the translation.\n"
        f"Text: {text}\n"
        f"Translation:"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # Cero creatividad
            "num_ctx": 4096
        }
    }
    
    try:
        res = requests.post(API_URL, json=payload, timeout=60)
        traduccion = res.json()['response'].strip()
        
        # Limpieza básica de chat
        if "Here is" in traduccion or "Translation:" in traduccion:
            traduccion = traduccion.split("\n")[-1] # Coger la última línea
            
        return traduccion
    except:
        return text

def procesar_archivo_completo(filepath, position):
    filename = os.path.basename(filepath)
    short_name = (filename[:15] + '..') if len(filename) > 15 else filename
    
    # 1. FASE DE REPARACIÓN (OCR)
    # Mostramos estado en la barra
    print(f"🔧 [{short_name}] Reparando texto (OCR)... Esto tarda un poco...", flush=True)
    ruta_reparada = reparar_pdf_ocr(filepath)
    
    # 2. FASE DE TRADUCCIÓN
    pdf_out_path = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        doc = fitz.open(ruta_reparada)
        total_pages = len(doc)
        
        with tqdm(total=total_pages, desc=f"Trad {short_name}", position=position, leave=False) as pbar:
            for page in doc:
                # blocks = (x0, y0, x1, y1, text, ...)
                blocks = page.get_text("blocks")
                
                for block in blocks:
                    rect = fitz.Rect(block[:4])
                    text_original = block[4].replace('\n', ' ').strip()
                    
                    if len(text_original) < 3: continue

                    # Traducimos el texto limpio (gracias al OCR)
                    text_translated = translate_text(text_original, MODEL_NAME)
                    
                    if text_translated != text_original:
                        # Borrar original
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        page.apply_redactions()
                        
                        # Escribir traducción
                        page.insert_textbox(
                            rect, 
                            text_translated, 
                            fontsize=9, 
                            fontname="helv", 
                            color=(0,0,0), 
                            align=0
                        )
                
                pbar.update(1)
        
        doc.save(pdf_out_path)
        doc.close()
        
        # Borrar el temporal del OCR para ahorrar espacio
        if ruta_reparada != filepath and os.path.exists(ruta_reparada):
            os.remove(ruta_reparada)
            
        return True, filepath

    except Exception as e:
        print(f"Error fatal en {filename}: {e}")
        return False, filepath

def main():
    setup_folders()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"--- TRADUCTOR FINAL (OCR + TRADUCCIÓN) ---")
    print("1. Repara el texto ruso corrupto (OCR).")
    print("2. Traduce al estilo directo.")
    print("3. Genera PDF con imágenes.")
    print("---------------------------------------------")
    
    while True:
        archivos = []
        for root, _, files in os.walk(INPUT_FOLDER):
            for file in files:
                if file.lower().endswith(".pdf"):
                    archivos.append(os.path.join(root, file))
        
        if not archivos:
            print("Esperando archivos... (Ctrl+C para salir)", end="\r")
            time.sleep(5)
            continue
            
        print(f"\n🚀 Procesando {len(archivos)} archivos...\n")
        
        # Usamos 2 workers porque el OCR gasta mucha CPU
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = []
            for i, archivo in enumerate(archivos):
                futures.append(executor.submit(procesar_archivo_completo, archivo, i % WORKERS))
            
            for future in as_completed(futures):
                exito, ruta = future.result()
                nombre = os.path.basename(ruta)
                if exito:
                    dest = os.path.join(PROCESSED_FOLDER, nombre)
                    if os.path.exists(dest):
                         base, ext = os.path.splitext(nombre)
                         dest = os.path.join(PROCESSED_FOLDER, f"{base}_{int(time.time())}{ext}")
                    shutil.move(ruta, dest)
                else:
                    shutil.move(ruta, os.path.join(ERROR_FOLDER, nombre))
                    
        print("\n✅ Lote terminado.")

if __name__ == "__main__":
    main()
