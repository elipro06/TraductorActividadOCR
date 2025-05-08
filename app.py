import streamlit as st
import os
import time
import glob
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
from googletrans import Translator

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #e0f7fa, #ffffff);
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }
    h1, h2, h3 {
        color: #006064;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def clear_old_audios(days):
    mp3_files = glob.glob("temp/*.mp3")
    now = time.time()
    limit = days * 86400
    for f in mp3_files:
        if os.stat(f).st_mtime < now - limit:
            os.remove(f)

clear_old_audios(7)
os.makedirs("temp", exist_ok=True)

st.markdown("<h1>🖼️ Texto en Imagen a Audio</h1>", unsafe_allow_html=True)
st.markdown("<p>Sube una imagen o usa la cámara para detectar texto y escucharlo traducido en tu idioma favorito.</p>", unsafe_allow_html=True)

use_camera = st.toggle("📷 Usar cámara")

if use_camera:
    image_buffer = st.camera_input("Captura una imagen")
else:
    image_buffer = None

with st.sidebar:
    st.header("⚙️ Opciones de Procesamiento")
    apply_filter = st.checkbox("Invertir colores para mejor OCR")
    st.markdown("---")
    st.header("🌐 Idioma y Voz")
    translator = Translator()
    lang_options = {
        "Español": "es", "Inglés": "en", "Francés": "fr",
        "Alemán": "de", "Italiano": "it", "Japonés": "ja"
    }
    input_lang = st.selectbox("Idioma de origen", list(lang_options.keys()))
    output_lang = st.selectbox("Idioma destino", list(lang_options.keys()))
    accents = {
        "Estándar": "com", "India": "co.in", "Reino Unido": "co.uk",
        "Canadá": "ca", "Australia": "com.au"
    }
    voice_region = st.selectbox("Acento", list(accents.keys()))
    show_translated_text = st.checkbox("Mostrar traducción de texto")

detected_text = ""

uploaded_img = st.file_uploader("📤 O sube una imagen desde tu dispositivo", type=["jpg", "png", "jpeg"])
if uploaded_img:
    img_bytes = uploaded_img.read()
    img_path = os.path.join("temp", uploaded_img.name)
    with open(img_path, 'wb') as f:
        f.write(img_bytes)
    st.image(img_path, caption="Imagen cargada", use_column_width=True)
    img_cv = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    detected_text = pytesseract.image_to_string(img_rgb)
    st.markdown("### 📝 Texto detectado:")
    st.write(detected_text)

if image_buffer:
    bytes_data = image_buffer.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    if apply_filter:
        cv_img = cv2.bitwise_not(cv_img)
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    detected_text = pytesseract.image_to_string(img_rgb)
    st.markdown("### 📝 Texto detectado:")
    st.write(detected_text)

def convert_text_to_audio(src_lang, dest_lang, content, region_tld):
    translated = translator.translate(content, src=src_lang, dest=dest_lang)
    translated_text = translated.text
    tts = gTTS(translated_text, lang=dest_lang, tld=region_tld, slow=False)
    filename = translated_text[:15].replace(" ", "_") + ".mp3"
    filepath = os.path.join("temp", filename)
    tts.save(filepath)
    return filepath, translated_text

if st.button("🔉 Escuchar traducción"):
    if detected_text.strip() == "":
        st.error("No se detectó texto. Intenta con otra imagen.")
    else:
        file_path, trans_text = convert_text_to_audio(
            lang_options[input_lang],
            lang_options[output_lang],
            detected_text,
            accents[voice_region]
        )
        audio = open(file_path, "rb")
        st.audio(audio.read(), format="audio/mp3")
        if show_translated_text:
            st.markdown("### 🌍 Traducción:")
            st.write(trans_text)
