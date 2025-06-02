import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import qrcode
from io import BytesIO

st.set_page_config(
    page_title="Optimeyes - Démo Profil Visuel",
    page_icon="👁️",  # tu peux aussi utiliser un chemin vers une image locale .ico ou .png
    layout="centered"
)

# --- CONFIGURATION ---
FICHIER_ITEMS = "Vivatech_Optimeyes.xlsx"
FICHIER_SORTIE = "donnees_patients.xlsx"
FEUILLE_ITEMS = "Sheet1"
COLONNE_ITEMS = "Item"

# --- CHARGEMENT DU FORMULAIRE ---
@st.cache_data
def charger_config_formulaire():
    df_items = pd.read_excel(FICHIER_ITEMS, sheet_name=FEUILLE_ITEMS)
    df_items.columns = [str(col).strip().capitalize() for col in df_items.columns]
    colonnes_attendues = ["Item", "Description", "Type", "Décimales", "Unité", "Options", "Min", "Max", "Default", "Step", "Question"]
    for col in colonnes_attendues:
        if col not in df_items.columns:
            df_items[col] = ""
    df_items = df_items[colonnes_attendues].fillna("")
    df_items = df_items[df_items["Item"].str.strip() != ""]
    return df_items

# --- PROFILING PONDÉRÉ ---
def scorer_profil(d):
    # Seuils pour scoring 0-3
    def noter(variable, valeur):
        if variable == "Decision_Visuelle":
            return 3 if valeur == "Rapide" else 2 if valeur == "Moyenne" else 1 if valeur == "Lente" else 0
        if variable == "Sensibilite_Lumineuse":
            return 3 if valeur == "Non" else 2 if valeur == "Parfois" else 1 if valeur == "Oui" else 0
        if variable == "Vision_Peri":
            return 3 if valeur == "Bon" else 2 if valeur == "Moyen" else 1 if valeur == "Faible" else 0
        if variable == "Vitesse_Horizontale":
            return 3 if 501 <= valeur <= 700 else 2 if (451 <= valeur <= 500 or 701 <= valeur <= 850) else 1 if valeur <= 450 or valeur > 850 else 0
        if variable == "Vitesse_Verticale":
            return 1 if valeur <= 300 else 2 if valeur <= 399 else 3 if valeur <= 9999 else 0
        if variable == "NOGO":
            return 3 if valeur <= 10 else 1 if valeur > 10 else 0
        if variable == "GO":
            return 3 if valeur <= 500 else 2 if valeur <= 599 else 1 if valeur <= 9999 else 0
        if variable == "Vision_Faible_Contraste":
            return 3 if valeur == 0 else 1 if valeur > 0 else 0
        if variable == "Fatigue_Visuelle":
            return 1 if 8 <= valeur <= 10 else 2 if 4 <= valeur <= 7 else 3 if 1 <= valeur <= 3 else 0
        if variable == "Sensibilite_Lumineuse":
            return 3 if valeur == 1 else 2 if valeur in [2, 3] else 1 if valeur in [4, 5] else 0
        if variable == "Vision_Peri":
            return 1 if valeur in [1, 2] else 2 if valeur in [3, 4] else 3 if valeur == 5 else 0
        return 0

    # Pondérations ajustées avec noms corrects
    poids = {
        "Athlète": {
            #"Fatigue_Visuelle": 2,
            "GO": 2,
            "NOGO": 2,
            "Vitesse_Horizontale": 2,
            "Vitesse_Verticale": 2,
            "Vision_Faible_Contraste": 1,
            "stereopsie": 3,
        },
        "Pilote": {
            #"Fatigue_Visuelle": 2,
            "GO": 2,
            "NOGO": 2,
            "Vitesse_Horizontale": 1,
            "Vitesse_Verticale": 1,
            "Vision_Faible_Contraste": 1,
            "stereopsie": 2
        },
        "E-sportif": {
            #"Fatigue_Visuelle": 2,
            "GO": 2,
            "NOGO": 2,
            "Vitesse_Horizontale": 4,
            "Vitesse_Verticale": 4,
            "Vision_Faible_Contraste": 1,
            "stereopsie": 2
        },
        "Performer cognitif": {
            #"Fatigue_Visuelle": 2,
            "GO": 2,
            "NOGO": 2,
            "Vitesse_Horizontale": 1,
            "Vitesse_Verticale": 1,
            "Vision_Faible_Contraste": 4,
            "stereopsie": 1
        }
    }

    scores = {}
    for profil, variables in poids.items():
        score = 0
        total_poids = sum(variables.values())
        for var, p in variables.items():
            score += noter(var, d.get(var, 0)) * p
        scores[profil] = round((score / (3 * total_poids)) * 100, 1)

    return {"profil": max(scores, key=scores.get), "scores": scores}

# --- INITIALISATION ---
if "donnees" not in st.session_state:
    try:
        df_exist = pd.read_excel(FICHIER_SORTIE)
        st.session_state.donnees = df_exist.to_dict(orient="records")
    except FileNotFoundError:
        st.session_state.donnees = []

st.title("👁 Démo Optimeyes – Vivatech")
df_config = charger_config_formulaire()

# --- FORMULAIRE DE SAISIE ---
with st.form("formulaire_saisie"):
    st.subheader("➕ Ajouter un nouveau sujet")
    saisie = {}

    for _, row in df_config.iterrows():
        description = row.get("Description").strip()
        if row.get("Question", "").strip():
            question = f"**{row['Question'].strip()}**"
            label = f"{description}\n\n{question}"
        else :
            label = description
        item = row[COLONNE_ITEMS]
        type_champ = str(row["Type"]).strip().lower()
        unite = str(row.get("Unité", "")).strip()
        options_raw = str(row["Options"]).strip()

        try:
            decimales = int(row["Décimales"])
        except:
            decimales = 1
        try:
            step = float(row["Step"])
        except:
            step = 1.0
        try:
            min_val = float(row["Min"])
        except:
            min_val = 0.0
        try:
            default = float(row["Default"])
        except:
            default = 0.0
        try:
            max_val = float(row["Max"])
        except:
            max_val = 100.0

        if default < min_val:
            default = min_val
        elif default > max_val:
            default = max_val

        options = [opt.strip() for opt in options_raw.split(";") if opt.strip()]

        if type_champ == "text":
            valeur = st.text_input(label, key=item)

        elif type_champ == "slider":
            valeur = st.slider(label, min_value=min_val, max_value=max_val, value=default, step=step, key=item)

        elif type_champ == "radio":
            valeur = st.radio(label, options, key=item)

        elif type_champ == "select":
            valeur = st.selectbox(label, options, key=item)

        elif type_champ == "multiselect":
            valeur = st.multiselect(label, options, key=item)

        elif type_champ in ["bool", "checkbox"]:
            valeur = st.checkbox(label, key=item)

        else:  # champ numérique par défaut
            format_str = f"%.{decimales}f"
            col1, col2 = st.columns([4, 1])
            with col1:
                valeur = st.number_input(label, value=default, format=format_str, step=step, min_value=min_val, max_value=max_val, key=item)
            with col2:
                st.markdown(f"<div style='margin-top: 2em;'>{unite}</div>", unsafe_allow_html=True)

        saisie[item] = valeur

    submitted = st.form_submit_button("Ajouter l'individu")

# --- RADAR ---
def afficher_radar(scores):
    labels = list(scores.keys())
    valeurs = list(scores.values())
    valeurs += valeurs[:1]
    angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(4,4), subplot_kw=dict(polar=True))
    ax.plot(angles, valeurs, linewidth=2)
    ax.fill(angles, valeurs, alpha=0.3)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    st.pyplot(fig)

# --- SOUMISSION ET TRAITEMENT DU PROFIL ---
if submitted:
    profil = scorer_profil(saisie)
    saisie["Profil"] = profil["profil"]
    for k, v in profil["scores"].items():
        saisie[f"Score_{k}"] = v

    st.session_state.donnees.append(saisie)
    df_total = pd.DataFrame(st.session_state.donnees)
    df_total.to_excel(FICHIER_SORTIE, index=False)
    st.success(f"✅ Participant ajouté. Profil dominant : **{profil['profil']}**")

    st.subheader("🎯 Résultat du Profiling")
    afficher_radar(profil["scores"])

    # --- QR CODE ---
    qr_content = f"Profil: {profil['profil']} | Code: {saisie.get('Code_Sujet')}"
    qr_img = qrcode.make(qr_content)
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    st.image(buffered.getvalue(), caption="Passeport visuel", width=200)
    st.download_button("📥 Télécharger passeport", data=buffered.getvalue(), file_name="passeport_visuel.png")

# --- AFFICHAGE DES DONNÉES ---
if st.session_state.donnees:
    df = pd.DataFrame(st.session_state.donnees)
    with st.sidebar:
        st.markdown("## 📊 Données collectées")
        sujets = df["Code_Sujet"].dropna().astype(str).unique().tolist()
        if sujets:
            selection = st.selectbox("👤 Choisir un sujet", options=sujets)
            donnees_sujet = df[df["Code_Sujet"].astype(str) == selection].head(1).transpose()
            donnees_sujet.columns = [selection]
            st.dataframe(donnees_sujet)
            colonnes_scores = [col for col in df.columns if col.startswith("Score_") and col.replace("Score_", "") in ["Athlète", "Pilote", "E-sportif", "Performer cognitif"]]
            if colonnes_scores:
                scores_selection = df[df["Code_Sujet"].astype(str) == selection][colonnes_scores].iloc[0].to_dict()
                scores_radar = {k.replace("Score_", ""): v for k, v in scores_selection.items()}
                st.markdown("### 🔎 Radar du profil sélectionné")
                afficher_radar(scores_radar)
        else:
            st.info("Aucun sujet identifié (Code_Sujet manquant).")
else:
    with st.sidebar:
        st.markdown("## 📊 Données collectées")
        st.info("Aucune donnée saisie pour le moment.")

# --- SUPPRESSION DE LIGNES ---
if st.session_state.donnees:
    st.subheader("🗑️ Supprimer une ou plusieurs lignes")
    lignes_identifiables = {
        f"{i+1} - {row.get('Code_Sujet', '(inconnu)')}": i
        for i, row in enumerate(st.session_state.donnees)
    }
    lignes_a_supprimer = st.multiselect("Sélectionner les individus à supprimer", options=list(lignes_identifiables.keys()))
    if lignes_a_supprimer and st.button("Supprimer les lignes sélectionnées"):
        indices = [lignes_identifiables[label] for label in lignes_a_supprimer]
        st.session_state.donnees = [row for i, row in enumerate(st.session_state.donnees) if i not in indices]
        df_maj = pd.DataFrame(st.session_state.donnees)
        df_maj.to_excel(FICHIER_SORTIE, index=False)
        st.success("🗑️ Lignes supprimées avec succès")
