import streamlit as st
import os
import shutil
from engine import create_blind_schema

# 1. Création automatique du dossier de la banque s'il n'existe pas
BANQUE_DIR = "banque_schemas"
if not os.path.exists(BANQUE_DIR):
    os.makedirs(BANQUE_DIR)

st.set_page_config(page_title="App IFMEM - Révision Ostéo", page_icon="🦴", layout="wide")
st.title("Générateur de Schémas Vierges 🦴")

# Initialisation de la mémoire
if 'schema_ready' not in st.session_state:
    st.session_state['schema_ready'] = False
    st.session_state['true_labels'] = []
if 'current_img_path' not in st.session_state:
    st.session_state['current_img_path'] = ""

# Barre latérale pour gérer les modes
st.sidebar.header("📚 Menu")
mode = st.sidebar.radio("Source de l'image :", ["Importer une nouveauté", "Ouvrir depuis la banque"])

# Lecture des images déjà sauvegardées dans le dossier
fichiers_banque = [f for f in os.listdir(BANQUE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
image_a_traiter = None

if mode == "Importer une nouveauté":
    uploaded_file = st.file_uploader("Prends une photo ou importe un schéma", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image_a_traiter = "temp_input.jpg"
        with open(image_a_traiter, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Petit formulaire pour enregistrer dans la banque
        col_save1, col_save2 = st.columns([3, 1])
        with col_save1:
            nom_fichier = st.text_input("Nom pour enregistrer dans la banque (ex: crane_face) :")
        with col_save2:
            st.write("") # Espacement visuel
            st.write("")
            if st.button("💾 Sauvegarder dans la banque"):
                if nom_fichier:
                    chemin_sauvegarde = os.path.join(BANQUE_DIR, f"{nom_fichier}.jpg")
                    shutil.copy(image_a_traiter, chemin_sauvegarde)
                    st.success(f"Sauvegardé ! ({nom_fichier}.jpg)")
                    st.rerun()

else:
    if len(fichiers_banque) == 0:
        st.info("La banque est vide. Importe et sauvegarde d'abord un schéma via le menu de gauche.")
    else:
        image_choisie = st.selectbox("Choisis un schéma à réviser :", fichiers_banque)
        image_a_traiter = os.path.join(BANQUE_DIR, image_choisie)

# --- Zone de traitement et d'exercice ---
if image_a_traiter:
    # Si on change de schéma dans la liste, on efface l'exercice précédent
    if st.session_state['current_img_path'] != image_a_traiter:
        st.session_state['schema_ready'] = False
        st.session_state['current_img_path'] = image_a_traiter

    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("👀 Voir le schéma original (Attention triche !)", expanded=False):
            st.image(image_a_traiter, use_container_width=True)
            
        if st.button("Créer l'exercice", type="primary"):
            with st.spinner("Analyse, effacement et numérotation..."):
                output_path = "temp_output.jpg"
                # Lancement du moteur
                st.session_state['true_labels'] = create_blind_schema(image_a_traiter, output_path)
                st.session_state['schema_ready'] = True
                st.rerun()
                
    with col2:
        if st.session_state['schema_ready']:
            st.image("temp_output.jpg", caption="Schéma d'exercice", use_container_width=True)
            st.subheader("📝 À toi de jouer !")
            
            labels = st.session_state['true_labels']
            
            # Création dynamique des champs
            for i in range(len(labels)):
                st.text_input(f"Légende n°{i+1}", key=f"rep_{i}")
            
            st.markdown("---")
            
            if st.button("Vérifier mes réponses", type="primary"):
                st.subheader("Correction :")
                score = 0
                for i, vrai_texte in enumerate(labels):
                    reponse_user = st.session_state.get(f"rep_{i}", "").strip().lower()
                    vrai_texte_propre = vrai_texte.strip().lower()
                    
                    if reponse_user and (reponse_user in vrai_texte_propre or vrai_texte_propre in reponse_user):
                        st.success(f"N°{i+1} : ✅ Correct ! ({vrai_texte})")
                        score += 1
                    else:
                        st.error(f"N°{i+1} : ❌ Faux. La réponse était : **{vrai_texte}**")
                        
                st.metric(label="Score final", value=f"{score} / {len(labels)}")