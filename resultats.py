import streamlit as st
import pandas as pd
from io import BytesIO
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURATION ---
FICHIER_ID_DRIVE = "TON_ID_DU_FICHIER_XLSX_SUR_DRIVE"

# --- Connexion au Google Drive ---
def connect_drive():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["google"],
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

# --- Télécharger le fichier Excel depuis Drive ---
@st.cache_data(ttl=60)
def telecharger_donnees():
    service = connect_drive()
    request = service.files().get_media(fileId=FICHIER_ID_DRIVE)
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buffer.seek(0)
    return pd.read_excel(buffer)

# --- Charger données à partir de l'URL ---
def charger_profil(url_id):
    df = telecharger_donnees()
    ligne = df[df["Url_ID"] == url_id]
    return ligne

# --- Interface ---
st.set_page_config(page_title="Passeport Visuel Optimeyes", layout="centered")
st.image("optimeyes_logo_black.png", width=400)

st.title("🎫 Passeport Visuo-Cognitif")

# --- Récupérer l'ID de l'URL ---
params = st.experimental_get_query_params()
url_id = params.get("id", [None])[0]

if not url_id:
    st.error("❌ Aucun identifiant de profil fourni dans l'URL.")
    st.stop()

# --- Charger les données ---
ligne = charger_profil(url_id)

if ligne.empty:
    st.error("❌ Profil introuvable. Vérifiez votre lien.")
    st.stop()

# --- Affichage des données ---
profil = ligne.iloc[0].get("Profil", "Profil inconnu")
score_global = ligne.iloc[0].get("Score_Global", "?")
coherence = ligne.iloc[0].get("Coherence", "?")

st.markdown(f"""
## 👁️ Profil dominant : **{profil}**

- 🎯 Score global : **{score_global} %**
- 🔍 Cohérence subjectif/performance : **{coherence}**
""")

# --- Option : Radar ou résumé analytique ---
try:
    radar = ligne.iloc[0].get("Radar_Analytique", {})
    if isinstance(radar, str):
        radar = eval(radar)
    if isinstance(radar, dict):
        st.subheader("🔬 Répartition analytique")
        st.bar_chart(pd.Series(radar))
except Exception as e:
    st.info("Radar non disponible.")

st.markdown("---")
st.info("Ce résultat est issu de l'expérience Optimeyes VivaTech 2025.")
