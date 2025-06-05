import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import qrcode
import numpy as np
from io import BytesIO
import plotly.graph_objects as go

FICHIER_ITEMS = "Vivatech_Optimeyes.csv"
FICHIER_SORTIE = "donnees_patients.xlsx"
FEUILLE_ITEMS = "Sheet1"
COLONNE_ITEMS = "Item"

# --- PARAMETRES ---

commentaires_indicateurs = {
    "Decision_Visuelle": {
        3: "Décision très rapide, excellente réactivité.",
        2: "Décision de vitesse moyenne, correcte dans l’ensemble.",
        1: "Décision lente, réactivité diminuée.",
    },
    "Fatigue_Visuelle": {
        3: "Très faible fatigue visuelle ressentie.",
        2: "Fatigue visuelle modérée.",
        1: "Fatigue visuelle importante signalée.",
    },
    "Sensibilite_Lumineuse": {
        3: "Aucune sensibilité à la lumière signalée.",
        2: "Sensibilité occasionnelle à la lumière.",
        1: "Sensibilité marquée à la lumière.",
    },
    "Vision_Peri": {
        3: "Vision périphérique jugée bonne.",
        2: "Vision périphérique moyenne.",
        1: "Vision périphérique faible.",
    },
    "Confort_Visuel": {
        3: "Très bon confort visuel perçu.",
        2: "Confort visuel acceptable.",
        1: "Confort visuel faible ou inconfort.",
    },
    "Vitesse_Horizontale": {
        3: "Excellente vitesse visuelle horizontale.",
        2: "Vitesse correcte avec marge de progression.",
        1: "Vitesse visuelle lente ou perturbée.",
    },
    "Vitesse_Verticale": {
        3: "Très bonne vitesse visuelle verticale.",
        2: "Vitesse verticale modérée.",
        1: "Réduction marquée de la vitesse verticale.",
    },
    "Vision_Faible_Contraste": {
        3: "Aucune difficulté détectée en faible contraste.",
        2: "Légère difficulté avec les contrastes faibles.",
        1: "Difficulté importante à détecter les faibles contrastes.",
    },
    "Stereopsie": {
        3: "Excellente perception 3D (stéréopsie).",
        2: "Perception 3D correcte.",
        1: "Perception 3D altérée ou lente.",
    },
    "GO_NOGO": {
        3: "Très bon contrôle décisionnel (go/no-go).",
        2: "Contrôle correct avec vigilance.",
        1: "Décisions impulsives ou lenteur observée.",
    },
    "GO": {
        3: "Temps de réaction très rapide.",
        2: "Temps de réaction correct, mais améliorable.",
        1: "Temps de réaction lent ou erratique.",
    },
    "NOGO": {
        3: "Très bon contrôle inhibiteur (très peu d'erreurs).",
        2: "Contrôle correct avec quelques erreurs.",
        1: "Impulsivité marquée ou erreurs fréquentes.",
    }
}

def commenter_indicateur(variable, score):
    return commentaires_indicateurs.get(variable, {}).get(score, "")

# --- RADARS ---
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

def afficher_radar(valeurs, taille=(4, 4), titre=None):
    couleurs_profils = {
        "Athlète": "#90CBC1",
        "Pilote": "#A5B4DC",
        "E-sportif": "#D8A5B8",
        "Performer cognitif": "#B6A49C"
    }

    labels = list(valeurs.keys())
    donnees = list(valeurs.values())
    donnees += donnees[:1]  

    angles = [n / float(len(labels)) * 2 * np.pi for n in range(len(labels))]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=taille, subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#cccaca')  # fond gris clair

    # Courbe principale
    ax.plot(angles, donnees, linewidth=2, color='#444')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    # Colorier chaque secteur selon sa couleur de profil
    for i in range(len(labels)):
        angle0 = angles[i]
        angle1 = angles[i + 1]
        r = [0, donnees[i], donnees[i+1], 0]
        theta = [angle0, angle0, angle1, angle1]

        ax.fill(theta, r, color=couleurs_profils.get(labels[i], "#999"), alpha=0.25, linewidth=0)

    # Ajouter le titre si fourni
    if titre:
        ax.set_title(titre, fontsize=12, pad=20)

    st.pyplot(fig)
    
# --- GRAPHIQUES INDIVIDUELS --- #

def plot_jauge_multizone(nom, valeur, min_val, max_val, bornes_abs=[], custom_colors=None):
    # Couleurs par défaut (si aucune spécifique n’est fournie)
    default_colors = ["#ff4d4d", "#ff944d", "#ffd633", "#4caf50", "#2196f3", "#9c27b0"]
    couleurs = custom_colors if custom_colors else default_colors

    try:
        bornes = sorted([float(b) for b in bornes_abs if str(b).strip() != ""])
    except:
        bornes = []

    bornes = [min_val] + bornes + [max_val]
    zones = list(zip(bornes[:-1], bornes[1:]))

    fig, ax = plt.subplots(figsize=(5, 0.6))
    fig.patch.set_facecolor('#cccaca')  # Fond global du graphique
    ax.set_facecolor('#e0e0e0')         # Fond de la jauge (zone d’affichage)

    for i, (start, end) in enumerate(zones):
        color = couleurs[i] if i < len(couleurs) else "#cccccc"
        ax.barh(0, end - start, left=start, color=color, edgecolor="white")

    ax.axvline(valeur, color="#004080", linewidth=2)
    ax.text(
        valeur, -0.8,  # position (x, y), y en dessous de la barre horizontale
        f"{valeur:.0f}",  # texte affiché (arrondi entier)
        ha='center',
        va='top',
        fontsize=9,
        color="#004080",
        fontweight='bold'
    )
    ax.set_xlim(min_val, max_val)
    ax.set_yticks([])
    ax.set_xticks([min_val, max_val])
    ax.set_title(nom, fontsize=11, loc='left')
    for spine in ax.spines.values():
        spine.set_visible(False)

    return fig
    
# --- AFFICHAGE DES RESULTATS --- #

def afficher_resultats_complets(resultat, df_config, form_data):
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div style='background-color: #1e3a5f; padding: 20px; border-radius: 12px; text-align: center; color: white;'>
                    <h4 style='margin-bottom: 5px;'>🎯 Score de perception subjective</h4>
                    <div style='font-size: 2.5em; font-weight: bold; color: #66ccff;'>{resultat['indice_subjectif']} %</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style='background-color: #442b00; padding: 20px; border-radius: 12px; text-align: center; color: white;'>
                    <h4 style='margin-bottom: 5px;'>🧪 Score de performance clinique</h4>
                    <div style='font-size: 2.5em; font-weight: bold; color: #ffa64d;'>{resultat['indice_performance']} %</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Bloc de cohérence
    couleur_coherence = {
        "Très bonne": "#66ff99",
        "Moyenne": "#ffd966",
        "Faible": "#ff6666"
    }.get(resultat["coherence"], "#cccccc")

    st.markdown(
        f"""
        <div style='margin-top: 20px; padding: 15px; border-radius: 10px; background-color: #2a2a2a; color: white;'>
            <p style='margin: 0; font-size: 1.1em;'>
                🔍 <strong>Cohérence entre perception et performance :</strong>
                <span style='color: {couleur_coherence}; font-weight: bold;'> {resultat["coherence"]}</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Alerte si nécessaire
    if resultat["alerte_discordance"]:
        st.markdown(
            """
            <div style='margin-top: 10px; padding: 12px; border-radius: 8px; background-color: #5c0000; color: #ffe6e6; font-size: 0.95em;'>
                ⚠️ Attention : écart élevé entre perception et performance.
            </div>
            """,
            unsafe_allow_html=True
        )
        
    # PROFILAGE #    
    st.subheader("🎯 Résultat du Profiling")

    with st.container():
        col_g, col_d = st.columns([6, 4])

        with col_g:
            st.markdown("### 🔄 Score par profil")
            afficher_radar(resultat["scores"], titre="")

        with col_d:
            st.markdown("### 📋 Détail des scores")
            for profil, score in resultat["scores"].items():
                # Couleurs discrètes selon le profil
                badge_color = {
                    "Athlète": "#90CBC1",
                    "Pilote": "#A5B4DC",
                    "E-sportif": "#D8A5B8",
                    "Performer cognitif": "#B6A49C"
                }.get(profil, "#ccc")

                emoji = {
                    "Athlète": "🏃‍♂️",
                    "Pilote": "🏎️",
                    "E-sportif": "🎮",
                    "Performer cognitif": "🧠"
                }.get(profil, "👁️")

                st.markdown(
                    f"""
                    <div style='background-color:{badge_color};padding:8px 12px;margin-bottom:8px;
                                border-radius:8px;font-weight:600;color:#1f1f1f;'>
                        {emoji} {profil} : <span style='float:right;'>{score} %</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    st.markdown("---")
    
    # RADAR A 5 AXES #
    st.subheader("🔬 Analyse des 5 axes cognitifs et visuels")

    with st.container():
        col_g, col_d = st.columns([6, 4])

        with col_g:
            afficher_radar(resultat["radar_analytique"], titre="")

        with col_d:
            st.markdown("### 🧠 Scores par axe")
            for axe, score in resultat["radar_analytique"].items():
                couleur = "#e0e0e0"  # fond discret
                st.markdown(
                    f"""
                    <div style='background-color:{couleur};padding:8px 12px;margin-bottom:8px;
                                border-radius:8px;font-weight:600;color:#1f1f1f;'>
                        {axe} : <span style='float:right;'>{score} %</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    st.markdown("---")            
    # JAUGES INDIVIDUELLES DE PERFORMANCE #
    
    st.subheader("📏 Jauges de performance")

    indicateurs_jauge = [
        "Vitesse_Horizontale",
        "Vitesse_Verticale",
        "GO",
        "NOGO",
        "Vision_Faible_Contraste",
        "Stereopsie"
    ]

    donnees_individu = {
        item: float(form_data[item])
        for item in indicateurs_jauge
        if item in form_data and str(form_data[item]).strip() != ""
    }

    seuils_reference = {
        row["Item"]: {
            "min": float(row["Min"]),
            "max": float(row["Max"]),
            "borne1": row["Borne1"],
            "borne2": row["Borne2"],
            "borne3": row["Borne3"],
            "borne4": row["Borne4"]
        }
        for _, row in df_config.iterrows()
        if row["Item"] in indicateurs_jauge and str(row["Min"]).strip() and str(row["Max"]).strip()
    }

    col1, col2 = st.columns(2)
    compteur_affiches = 0  # compteur pour alterner proprement les colonnes
    
    for indicateur in donnees_individu:
        if indicateur == "Stereopsie" and not form_data.get("Stereopsie_activee", True):
            continue
    
        valeur = donnees_individu[indicateur]
        seuils = seuils_reference.get(indicateur, {"min": 0, "max": 100})
        bornes = [seuils.get(f"borne{i}") for i in range(1, 5)]
    
        # Couleurs adaptées
        great = "#66ccaa"     # vert doux
        good = "#b5d991"      # vert-jaune doux
        average = "#ffd580"   # beige doré
        bad = "#ff9c8a"       # corail
        worst = "#d66a6a"     # rouge doux
    
        if indicateur == "Stereopsie":
            couleurs = [bad, great, average, bad]
        elif indicateur == "Vitesse_Horizontale":
            couleurs = [bad, average, great, average, bad]
        elif indicateur == "Vitesse_Verticale":
            couleurs = [bad, average, great]
        elif indicateur == "GO":
            couleurs = [great, average, bad]
        elif indicateur == "NOGO":
            couleurs = [great, bad]
        elif indicateur == "Vision_Faible_Contraste":
            if valeur == 0:
                badge = "🟢 Bonne vision faible contraste"
                message = "Aucune difficulté détectée en faible contraste."
                couleur_fond = "#1e5631"
            else:
                badge = "🔴 Échec ou difficulté"
                message = "Difficulté à détecter les faibles contrastes."
                couleur_fond = "#8b1e3f"
    
            col = col1 if compteur_affiches % 2 == 0 else col2
            with col:
                st.markdown(
                    f"""
                    <div style='background-color: {couleur_fond}; padding: 16px; border-radius: 10px; text-align: center; color: white;'>
                        <div style='font-size: 1.1em; font-weight: bold;'>{badge}</div>
                        <p style='margin-top: 6px; font-size: 0.9em;'>{message}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            compteur_affiches += 1
            continue
        else:
            couleurs = None
    
        fig = plot_jauge_multizone(
            nom=indicateur,
            valeur=valeur,
            min_val=seuils["min"],
            max_val=seuils["max"],
            bornes_abs=bornes,
            custom_colors=couleurs
        )
    
        col = col1 if compteur_affiches % 2 == 0 else col2
        with col:
            st.pyplot(fig)
            commentaire = resultat["commentaires"].get(indicateur, "")
            if commentaire:
                st.markdown(f"<span style='font-size: 0.9em; color: grey;'>{commentaire}</span>", unsafe_allow_html=True)
        compteur_affiches += 1

# --- DEMARRAGE --- #
@st.cache_data
def charger_config_formulaire():
    df_items = pd.read_csv(FICHIER_ITEMS, sep=";",  encoding="latin1", engine="python")
    df_items.columns = [str(col).strip().capitalize() for col in df_items.columns]

    df_items["Page"] = pd.to_numeric(df_items["Page"], errors="coerce").fillna(0).astype(int)

    colonnes_attendues = ["Item", "Description", "Type", "Décimales", "Unité", "Options", "Min", "Max", "Default", "Step", "Borne1", "Borne2", "Borne3", "Borne4", "Bulle1", "Bulle2", "Question", "Page"]
    for col in colonnes_attendues:
        if col not in df_items.columns:
            df_items[col] = ""
    df_items = df_items[colonnes_attendues].fillna("")
    df_items = df_items[df_items["Item"].str.strip() != ""]
    return df_items

# Fonction de notation selon les valeurs observées
def noter(variable, valeur):
    if variable == "Decision_Visuelle":
        return 3 if valeur == "Rapide" else 2 if valeur == "Moyenne" else 1 if valeur == "Lente" else 0
    if variable == "Sensibilite_Lumineuse":
        return 3 if valeur == "Non" else 2 if valeur == "Parfois" else 1 if valeur == "Oui" else 0
    if variable == "Vision_Peri":
        return 3 if valeur == "Bon" else 2 if valeur == "Moyen" else 1 if valeur == "Faible" else 0
    if variable == "Vitesse_Horizontale" and isinstance(valeur, (int, float)):
        return 3 if 501 <= valeur <= 700 else 2 if (451 <= valeur <= 500 or 701 <= valeur <= 850) else 1 if valeur <= 450 or valeur > 850 else 0
    if variable == "Vitesse_Verticale" and isinstance(valeur, (int, float)):
        return 1 if valeur <= 300 else 2 if valeur <= 399 else 3 if valeur <= 9999 else 0
    if variable == "Vision_Faible_Contraste" and isinstance(valeur, (int, float)):
        return 3 if valeur == 0 else 1 if valeur > 0 else 0
    if variable == "Fatigue_Visuelle" and isinstance(valeur, (int, float)):
        return 1 if 8 <= valeur <= 10 else 2 if 4 <= valeur <= 7 else 3 if 1 <= valeur <= 3 else 0
    if variable == "Confort_Visuel" and isinstance(valeur, (int, float)):
        return 3 if 8 <= valeur <= 10 else 2 if 4 <= valeur <= 7 else 1 if 1 <= valeur <= 3 else 0
    if variable == "GO" and isinstance(valeur, (int, float)):
        return 3 if valeur <= 500 else 2 if valeur <= 700 else 1
    if variable == "NOGO" and isinstance(valeur, (int, float)):
        return 3 if valeur <= 5 else 2 if valeur <= 15 else 1
    if variable == "Stereopsie" and isinstance(valeur, (int, float)):
        return 3 if 30 <= valeur <= 60 else 2 if 61<= valeur <= 120 else 1 if valeur >= 121 else 0
    return 0
    
# --- DIVERS --- #

def noter_go_nogo(go, nogo):
    if go <= 500 and nogo <= 10:
        return 3
    elif go <= 500 and nogo > 10:
        return 2
    elif go > 500 and nogo <= 10:
        return 2
    else:
        return 1
        
# --- PROFILING PONDÉRÉ ---
def scorer_profil(d):
    
    # --- Partie 1 : Scores objectifs (avec pondération de GO_NOGO) ---
    go = d.get("GO")
    nogo = d.get("NOGO")
    go_nogo_score = noter_go_nogo(go, nogo) if go is not None and nogo is not None else 0

    stereopsie_activee = d.get("Stereopsie_activee", True)

    indicateurs_subjectifs = [
        "Decision_Visuelle", "Fatigue_Visuelle",
        "Sensibilite_Lumineuse", "Vision_Peri", "Confort_Visuel"
    ]
    score_subjectif_total = sum([noter(var, d.get(var, 0)) for var in indicateurs_subjectifs])
    indice_subjectif = round((score_subjectif_total / (3 * len(indicateurs_subjectifs))) * 100, 1)

    indicateurs_perf = ["Vitesse_Horizontale", "Vitesse_Verticale", "Vision_Faible_Contraste"]
    if stereopsie_activee:
        indicateurs_perf.append("Stereopsie")

    score_perf_total = sum([noter(var, d.get(var, 0)) for var in indicateurs_perf]) + (2 * go_nogo_score)
    total_points_theoriques = (len(indicateurs_perf) + 2) * 3
    indice_performance = round((score_perf_total / total_points_theoriques) * 100, 1)

    poids_subjectif = 0.4
    amplification = min(abs(indice_subjectif - indice_performance) / 100, 0.6)
    poids_performance = 1.0 - poids_subjectif + amplification
    poids_total = poids_subjectif + poids_performance
    poids_subjectif /= poids_total
    poids_performance /= poids_total
    score_global = round(poids_subjectif * indice_subjectif + poids_performance * indice_performance, 1)

    poids = {
        "Athlète": {
            "GO_NOGO": 2,
            "Vitesse_Horizontale": 2,
            "Vitesse_Verticale": 2,
            "Vision_Faible_Contraste": 1,
            "Stereopsie": 3,
        },
        "Pilote": {
            "GO_NOGO": 2,
            "Vitesse_Horizontale": 1,
            "Vitesse_Verticale": 1,
            "Vision_Faible_Contraste": 1,
            "Stereopsie": 2
        },
        "E-sportif": {
            "GO_NOGO": 2,
            "Vitesse_Horizontale": 4,
            "Vitesse_Verticale": 4,
            "Vision_Faible_Contraste": 1,
            "Stereopsie": 2
        },
        "Performer cognitif": {
            "GO_NOGO": 2,
            "Vitesse_Horizontale": 1,
            "Vitesse_Verticale": 1,
            "Vision_Faible_Contraste": 4,
            "Stereopsie": 1
        }
    }

    scores = {}

    for profil, variables in poids.items():
        score = 0
        total_poids = 0
        for var, p in variables.items():
            if var == "Stereopsie" and not stereopsie_activee:
                continue
            valeur = go_nogo_score if var == "GO_NOGO" else d.get(var, 0)
            score += noter(var, valeur) * p
            total_poids += p
        scores[profil] = round((score / (3 * total_poids)) * 100, 1) if total_poids else 0

    profil_dominant = max(scores, key=scores.get)
    score_profil_dominant = scores[profil_dominant]

    ecart = abs(indice_subjectif - indice_performance)
    coherence = (
        "Très bonne" if ecart < 10 else
        "Moyenne" if ecart < 25 else
        "Faible"
    )
    alerte_discordance = ecart >= 25
    
    # --- Partie 4 : Score radar analytique (5 axes) ---
    radar_analytique = {
        "Vitesse visuelle": round((noter("Vitesse_Horizontale", d.get("Vitesse_Horizontale", 0)) + noter("Vitesse_Verticale", d.get("Vitesse_Verticale", 0))) / 2 * 33.33, 1),
        "Résolution spatiale": round((noter("Vision_Faible_Contraste", d.get("Vision_Faible_Contraste", 0)) + (noter("Stereopsie", d.get("Stereopsie", 0)) if stereopsie_activee else 0)) / (2 if stereopsie_activee else 1) * 33.33, 1),
        "Attention périphérique": round(noter("Vision_Peri", d.get("Vision_Peri", 0)) * 33.33, 1),
        "Engagement décisionnel": round((go_nogo_score + noter("Decision_Visuelle", d.get("Decision_Visuelle", 0))) / 2 * 33.33, 1),
        "Surcharge visuelle perçue": round((noter("Fatigue_Visuelle", d.get("Fatigue_Visuelle", 0)) + noter("Sensibilite_Lumineuse", d.get("Sensibilite_Lumineuse", 0))) / 2 * 33.33, 1)
    }
    
    # --- Partie 5 : Commentaires par indicateur ---
    commentaires = {}
    for var in indicateurs_subjectifs + indicateurs_perf:
        if var == "Stereopsie" and not stereopsie_activee:
            continue
        score = noter(var, d.get(var, 0))
        commentaires[var] = commentaires_indicateurs.get(var, {}).get(score, "Interprétation non disponible.")
    commentaires["GO_NOGO"] = commentaires_indicateurs.get("GO_NOGO", {}).get(go_nogo_score, "Interprétation non disponible.")
    commentaires["GO"] = commentaires_indicateurs.get("GO", {}).get(noter("GO", go), "Interprétation non disponible.")
    commentaires["NOGO"] = commentaires_indicateurs.get("NOGO", {}).get(noter("NOGO", nogo), "Interprétation non disponible.")
    # GO/NOGO séparément car combiné

    return {
        "profil": profil_dominant,
        "scores": scores,
        "score_profil_dominant": score_profil_dominant,
        "indice_subjectif": indice_subjectif,
        "indice_performance": indice_performance,
        "score_global": score_global,
        "coherence": coherence,
        "radar_analytique": radar_analytique,
        "alerte_discordance": alerte_discordance,
        "commentaires": commentaires
    }

def afficher_page_formulaire():
    df_config = charger_config_formulaire()

    if "page" not in st.session_state:
        st.session_state.page = 0
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    page = st.session_state.page

    st.image("optimeyes_logo_black.png", width=600)
    st.subheader("Évaluation Visuo-Cognitive")
    
    with st.container():
        menu = st.columns([1, 1, 1])
        with menu[0]:
            st.button("🏠 Accueil", on_click=lambda: st.session_state.update({"page": 0}))
        with menu[1]:
            st.button("📊 Données", on_click=lambda: st.session_state.update({"page": 3}))
        with menu[2]:
            st.button("📝 Saisie", on_click=lambda: st.session_state.update({"page": 0.3}))
    
    if page == 0:
        with st.expander("📄 Présentation de l’expérience Optimeyes à VivaTech 2025", expanded=True):
            with st.container():
                st.markdown("## 🎯 Expérience Optimeyes à VivaTech 2025")
                st.markdown("*Le 14 juin – Stand Orange – Paris Expo Porte de Versailles*")

                st.markdown("**Et si vous découvriez en 5 minutes ce que vos yeux disent de vos performances ?**")

                st.markdown("""\
                À l’occasion de VivaTech 2025, Optimeyes propose une expérience immersive et ludique pour révéler le potentiel visuo-cognitif de chaque visiteur.

                Grâce à une interface intelligente de profilage et à des tests de perception interactifs, vous pourrez explorer les capacités souvent invisibles… mais pourtant essentielles à vos performances.
                """)

                st.markdown("### 🧪 Ce que vous allez vivre :")
                st.markdown("1. **Une auto-évaluation rapide et intuitive**  \nVia un formulaire digital, vous répondrez à quelques questions clés sur votre confort visuel, votre sensibilité à la lumière, ou votre capacité d’attention périphérique. Un moyen simple de débuter une introspection… par les yeux.")
                st.markdown("2. **Un test express en live avec eye-tracking**  \nEn moins de 3 minutes, vous serez invité à réaliser quelques exercices visuels et attentionnels, incluant :")
                st.markdown("""\
                - Des mesures de vitesse saccadique (horizontal & vertical)  
                - Un test Go/No-Go (réactivité & inhibition)  
                - Un test de vision à faible contraste, avec déclenchement d’un test de stéréopsie si besoin""")

                st.markdown("3. **La révélation de votre profil visuo-cognitif**  \nEn croisant vos résultats, l’algorithme Optimeyes vous attribuera un profil dominant parmi les quatre grands archétypes :")

                st.markdown("""\
                🏃‍♂️ Athlète de terrain  
                🧠 Performer cognitif  
                🎮 E-sportif  
                🏎️ Pilote  
                """)

                st.markdown("Chaque profil est accompagné d’un retour visuel simplifié (code couleur & jauges) pour mieux comprendre vos forces actuelles et vos axes de progression.")

                st.markdown("### 🎫 Bonus : Votre passeport visuel virtuel")
                st.markdown("""\
                À la fin du test, vous repartez avec un passeport numérique visuo-cognitif : une fiche synthétique de vos performances visuelles, qui pourra à terme être enrichie et suivie dans le temps.

                Une innovation pensée pour les coachs, préparateurs mentaux, professionnels de santé… et tous ceux qui souhaitent faire de la vision un outil stratégique de prévention, d’optimisation et d’accompagnement.
                """)

                st.markdown("### 🔍 Pourquoi c’est innovant ?")
                st.markdown("""\
                Parce que la vision n’est pas un simple sens, c’est un système de traitement de l’information.

                Et demain, la performance ne reposera plus seulement sur la force ou l’endurance, mais sur la capacité à voir, décider et agir en un éclair.
                """)

                st.markdown("👉 **Rejoignez-nous le 14 juin pour expérimenter ce futur… avec les yeux grands ouverts 👁️✨**")

    
    elif page in [0.3, 1]:
        titre = "➕ Page 1 : Questionnaire subjectif" if page == 0.3 else "🔬 Page 2 : Tests cliniques"
        st.subheader(titre)

        with st.form("formulaire_saisie"):
            saisie = {}
            page_config = df_config[df_config["Page"] == (1 if page == 0.3 else 2)]

            for _, row in page_config.iterrows():
                description = row.get("Description").strip()
                if row.get("Question", "").strip():
                    question = f"**{row['Question'].strip()}**"
                    label = f"{description}\n\n{question}"
                else:
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
                    bulle1 = str(row["Bulle1"]).strip()
                    bulle2 = str(row["Bulle2"]).strip()
                    col_g, col_c, col_d = st.columns([2, 6, 2])
                    with col_g:
                        st.markdown(f"<span style='font-size: 0.8em;'>{bulle1}</span>", unsafe_allow_html=True)
                    with col_d:
                        st.markdown(f"<span style='font-size: 0.8em; float: right;'>{bulle2}</span>", unsafe_allow_html=True)

                elif type_champ == "radio":
                    valeur = st.radio(label, options, key=item)

                elif type_champ == "select":
                    valeur = st.selectbox(label, options, key=item)

                elif type_champ == "multiselect":
                    valeur = st.multiselect(label, options, key=item)

                elif type_champ in ["bool", "checkbox"]:
                    valeur = st.checkbox(label, key=item)

                else:
                    format_str = f"%.{decimales}f"
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        valeur = st.number_input(label, value=default, format=format_str, step=step, min_value=min_val, max_value=max_val, key=item)
                    with col2:
                        st.markdown(f"<div style='margin-top: 2em;'>{unite}</div>", unsafe_allow_html=True)

                if item == "Stereopsie":
                    st.markdown("Souhaitez-vous inclure la stéréopsie dans l'analyse ?")
                    saisie["Stereopsie_activee"] = st.checkbox("Inclure la stéréopsie", value=False)

                st.markdown("---")
                saisie[item] = valeur

            submit = st.form_submit_button("Page suivante" if page == 0.3 else "Afficher les résultats")
            if submit:
                st.session_state.form_data.update(saisie)
                if page == 0.3 :
                    st.session_state.page = 0.5
                elif page == 0.5:
                    st.session_state.page = 1                
                else :
                    st.session_state.page = 2    
                st.rerun()
                
    elif page == 0.5:
        st.subheader("🔎 Résultats subjectifs intermédiaires")

        resultat_temp = scorer_profil(st.session_state.form_data)

        st.metric("Indice subjectif", f"{resultat_temp['indice_subjectif']} %")

        st.markdown("#### Radar subjectif (auto-évaluation)")

        indicateurs_subjectifs = [
            "Decision_Visuelle", "Fatigue_Visuelle",
            "Sensibilite_Lumineuse", "Vision_Peri", "Confort_Visuel"
        ]

        radar_subjectif = {
            var: noter(var, st.session_state.form_data.get(var, 0))
            for var in indicateurs_subjectifs
        }

        afficher_radar(radar_subjectif)

        st.markdown("---")

        if resultat_temp["indice_subjectif"] <= 50:
            st.success("Niveau de confort subjectif faible. La stéréopsie est proposée.")
        else:
            st.warning("Confort visuel perçu satisfaisant. La stéréopsie est optionnelle.")

        if st.button("Poursuivre avec les tests cliniques"):
            st.session_state.page = 1
            st.rerun()

        st.markdown("---")

    elif page == 2: 
        # Afficher les résultats
        if "resultat" not in st.session_state:
            st.session_state["resultat"] = scorer_profil(st.session_state.form_data)

        afficher_resultats_complets(
            st.session_state["resultat"], df_config, st.session_state.form_data
        )
        
        st.markdown("---")            

        email = st.text_input("Souhaitez-vous recevoir un récapitulatif ou donner votre avis ? (e-mail facultatif)")
        # Enregistrer avec clique sur un bouton
        if st.button("Valider et enregistrer"):
            donnee_complete = st.session_state.form_data.copy()
            donnee_complete.update({
                "Profil": st.session_state.resultat["profil"],
                "Score_Profil_Dominant": st.session_state.resultat["score_profil_dominant"],
                "Indice_Subjectif": st.session_state.resultat["indice_subjectif"],
                "indice_Performance": st.session_state.resultat["indice_performance"],
                "Score_Global": st.session_state.resultat["score_global"],
                "Coherence": st.session_state.resultat["coherence"],
                "Radar_Analytique": st.session_state.resultat["radar_analytique"],
                "Alerte_Discordance": st.session_state.resultat["alerte_discordance"],
                "Email": email
            })

            for k, v in st.session_state.resultat["scores"].items():
                donnee_complete[f"Score_{k}"] = v

            df_ligne = pd.DataFrame([donnee_complete])
            try:
                df_exist = pd.read_excel(FICHIER_SORTIE)
                df_new = pd.concat([df_exist, df_ligne], ignore_index=True)
            except FileNotFoundError:
                df_new = df_ligne
            df_new.to_excel(FICHIER_SORTIE, index=False)

            st.success("✅ Résultat enregistré.")

    elif page == 3:
        st.subheader("📊 Données enregistrées")

        try:
            df = pd.read_excel(FICHIER_SORTIE)
            df.reset_index(drop=True, inplace=True)

            # Ajout d'une colonne de sélection
            df_affichage = df.copy()
            df_affichage["✅ Sélectionner"] = False
            
            cols = ["✅ Sélectionner"] + [col for col in df_affichage.columns if col != "✅ Sélectionner"]
            df_affichage = df_affichage[cols]

            # Initialisation des cases si non déjà fait
            if "select_all" not in st.session_state:
                st.session_state.select_all = False
            if "deselect_all" not in st.session_state:
                st.session_state.deselect_all = False

            # Boutons d'action
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("✅ Tout sélectionner"):
                    st.session_state.select_all = True
                    st.session_state.deselect_all = False
            with col_b2:
                if st.button("❌ Tout désélectionner"):
                    st.session_state.select_all = False
                    st.session_state.deselect_all = True

            # Mise à jour des cases à cocher
            if st.session_state.select_all:
                df_affichage["✅ Sélectionner"] = True
            elif st.session_state.deselect_all:
                df_affichage["✅ Sélectionner"] = False


            edited_df = st.data_editor(
                df_affichage,
                use_container_width=True,
                num_rows="fixed",
                hide_index=True,
                key="table_donnees",
            )

            # Extraction des lignes sélectionnées
            lignes_selectionnees = edited_df[edited_df["✅ Sélectionner"] == True]
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Données")
                output.seek(0)
            st.download_button(
                    label="📥 Télécharger toutes les données (Excel)",
                    data=output,
                    file_name="donnees_patients.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            if not lignes_selectionnees.empty:
                st.success(f"{len(lignes_selectionnees)} ligne(s) sélectionnée(s)")
                
                # Fichier Excel pour lignes sélectionnées
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    lignes_selectionnees.to_excel(writer, index=False, sheet_name="Sélection")
                    buffer.seek(0)

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🗑️ Supprimer les lignes sélectionnées"):
                        indices_a_supprimer = lignes_selectionnees.index
                        df_new = df.drop(index=indices_a_supprimer).reset_index(drop=True)
                        df_new.to_excel(FICHIER_SORTIE, index=False)
                        st.success("Lignes supprimées. Recharge en cours...")
                        st.rerun()
                    
                    st.download_button(
                    label="📥 Télécharger les lignes sélectionnées (Excel)",
                    data=buffer,
                    file_name="donnees_selectionnees.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                if st.button("📈 Voir l’analyse des lignes sélectionnées"):
                    for i in lignes_selectionnees.index:
                        ligne = df.iloc[i].to_dict()

                        radar = ligne.get("Radar_Analytique", {})
                        if isinstance(radar, str):
                            try:
                                radar = eval(radar)
                            except:
                                radar = {}
                        resultat = scorer_profil(ligne)
                        code_sujet = ligne.get("Code_Sujet", f"Ligne {i+1}")
                        st.markdown(f"---\n### 📌 Résultats pour le sujet : {code_sujet}")
                        afficher_resultats_complets(resultat, df_config, ligne)

            else:
                st.info("Aucune ligne sélectionnée pour le moment.")

        except FileNotFoundError:
            st.warning("Aucune donnée trouvée.")
            
PASSWORD = "demooptimeyes"

if "acces_autorisé" not in st.session_state:
    st.session_state["acces_autorisé"] = False

if not st.session_state["acces_autorisé"]:
    # 🔓 Afficher le champ de mot de passe uniquement si non connecté
    mdp = st.text_input("🔒 Entrez le mot de passe :", type="password")
    if st.button("Valider"):
        if mdp == PASSWORD:
            st.session_state["acces_autorisé"] = True
            st.success("✅ Accès autorisé.")
            st.rerun()
        else:
            st.error("❌ Mot de passe incorrect.")
else:
    # ✅ On n’affiche plus rien du tout une fois connecté
    afficher_page_formulaire()
