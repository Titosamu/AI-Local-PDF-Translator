# 🚀 AI Local PDF Translator & OCR

Herramienta profesional para traducir documentos PDF masivos de forma 100% local, preservando imágenes, tablas y maquetación original. Combina la potencia de **Ollama** (LLMs locales), **OCRmyPDF** (Reparación de texto) y **PyMuPDF**.
<img width="604" height="270" alt="traductor" src="https://github.com/user-attachments/assets/3ef14136-0055-4715-a29f-21c00a7e27e8" />
<img width="1047" height="256" alt="traductor1" src="https://github.com/user-attachments/assets/d6400b2a-7d4a-4430-8195-e8d49929f17c" />

## ✨ Características Principales

- **Privacidad Total:** Todo se ejecuta en tu servidor o PC local. Ningún dato sale a la nube.
- **OCR Integrado:** Detecta y repara automáticamente PDFs escaneados o con codificación corrupta antes de traducir.
- **Anti-Alucinaciones:** Sistema de prompts optimizados y limpieza de respuestas para evitar que la IA "hable" de más.
- **Gestión Inteligente de RAM:** Procesamiento por lotes (`Batch Processing`) y limpieza automática de memoria (`Garbage Collection`) para procesar miles de archivos sin saturar el sistema.
- **Multiproceso:** Soporte configurable para múltiples workers simultáneos.

## 🛠️ Requisitos Previos

Para usar esta herramienta necesitas:

1. **Python 3.10** o superior.
2. **[Ollama](https://ollama.com)** instalado y ejecutándose en segundo plano.
3. **Dependencias del sistema** (necesarias para el OCR y conversión):
   
   *En Ubuntu/Debian:*
   ```bash
   sudo apt-get update
   sudo apt-get install -y ocrmypdf tesseract-ocr-rus libreoffice
   ```
   *(Nota: Instala `tesseract-ocr-rus` si traduces ruso, o el idioma que corresponda).*

## 📦 Instalación

1. Clona este repositorio:
   ```bash
   git clone [https://github.com/TU_USUARIO/AI-Local-PDF-Translator.git](https://github.com/TU_USUARIO/AI-Local-PDF-Translator.git)
   cd AI-Local-PDF-Translator
   ```

2. Instala las librerías de Python necesarias:
   ```bash
   pip install -r requirements.txt
   ```

3. Descarga el modelo de IA (Recomendado: Gemma 2 9b):
   ```bash
   ollama pull gemma2:9b
   ```

## 🚀 Uso

### 1. Traducción de PDFs
Coloca tus archivos PDF en la carpeta `ENTRADA_PDFS` (si no existe, el script la creará en la primera ejecución). Luego ejecuta:

```bash
python3 main.py
```
Los archivos traducidos aparecerán automáticamente en la carpeta `SALIDA_TRADUCIDOS`.

### 2. Conversión de Office a PDF
Si tienes archivos de Word (`.docx`) o PowerPoint (`.pptx`):

1. Colócalos en la carpeta `ENTRADA_OFFICE`.
2. Ejecuta el script auxiliar:
   ```bash
   python3 office_to_pdf.py
   ```
3. Los archivos se convertirán a PDF y se moverán automáticamente a la cola de traducción.

## ⚙️ Configuración Avanzada

Puedes editar las variables al inicio del archivo `main.py` para ajustar el rendimiento:

- **WORKERS:** Número de archivos simultáneos (Por defecto: 3 o 4 según tu VRAM).
- **BATCH_SIZE:** Cada cuántos archivos se limpia la memoria RAM (Ideal para lotes de +1000 archivos).
- **MODEL_NAME:** Cambia el modelo de Ollama (ej. `llama3`, `mistral`).

---
**Nota:** Este proyecto fue diseñado para entornos de producción con alta carga de trabajo.
