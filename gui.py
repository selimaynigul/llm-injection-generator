import streamlit as st
import subprocess
import os
import pandas as pd
import time
import configparser

st.set_page_config(page_title="Injection Generator GUI", layout="wide")
st.title("🧬 Injection Generator GUI")

st.markdown("Bu arayüz üzerinden Genetic Algorithm ve GAN modellerini başlatabilir, sonuçları görüntüleyebilirsiniz.")

# Config oku
config = configparser.ConfigParser()
config.read("config.ini")
max_try_num = int(config['Genetic']['max_try_num'])

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return process

def display_output(process, progress_bar, status_text, log_area):
    logs = ""
    line_count = 0
    while True:
        line = process.stdout.readline()
        if not line:
            break
        logs += line
        log_area.text_area("Canlı Loglar", logs, height=400)
        line_count += 1
        progress_bar.progress(min(line_count / (max_try_num * 20), 1.0))
        status_text.text(f"İşlem devam ediyor... {int(min(line_count / (max_try_num * 20), 1.0) * 100)}%")
    process.stdout.close()
    process.wait()
    progress_bar.progress(1.0)
    status_text.text("Tamamlandı ✅")

# GA başlat
if st.button("🔁 Start Genetic Algorithm"):
    st.info("Genetic Algorithm başlatılıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.empty()
    process = run_command(["python", "generator.py"])
    display_output(process, progress_bar, status_text, log_area)

# GAN başlat
if st.button("🧠 Start GAN"):
    st.info("GAN başlatılıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.empty()
    process = run_command(["python", "gan_main.py"])
    display_output(process, progress_bar, status_text, log_area)

st.markdown("---")

# GA sonuçlarını göster
st.subheader("📁 GA Result Viewer")
result_files = os.listdir("result")
ga_files = [f for f in result_files if f.startswith("ga_result") and f.endswith(".csv")]

if ga_files:
    selected_ga = st.selectbox("Bir GA sonuç dosyası seçin:", ga_files)
    df_ga = pd.read_csv(os.path.join("result", selected_ga))
    st.dataframe(df_ga)
else:
    st.warning("Hiç GA sonucu bulunamadı.")

# GAN sonuçlarını göster
st.subheader("📁 GAN Result Viewer")
gan_files = [f for f in result_files if f.startswith("gan_result") and f.endswith(".csv")]

if gan_files:
    selected_gan = st.selectbox("Bir GAN sonuç dosyası seçin:", gan_files)
    df_gan = pd.read_csv(os.path.join("result", selected_gan))
    st.dataframe(df_gan)
else:
    st.warning("Hiç GAN sonucu bulunamadı.")
