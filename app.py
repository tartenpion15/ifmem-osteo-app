import streamlit as st
import os
import shutil
import json
from engine import create_blind_schema

# --- CONFIGURATION INITIALE ---
BANQUE_DIR = "banque_schemas"
if not os.path.exists(BANQUE_DIR):
    os.makedirs(BANQUE_DIR)

st.set_page_config(page_title="Révision Ostéo - IFMEM", page_icon="🦴", layout="wide")

# --- FONCTIONS UTILITAIRES ---
def get_score(nom_fichier):
    """Va lire le fichier JSON pour récupérer le meilleur score d'un schéma."""
    chemin_score = os.path.join(BANQUE_DIR, f"{nom_fichier}_score.json")
    if os.path.exists(chemin_score):
        try:
            with open(chemin_score, "r") as f:
                return json.load(f).get("meilleur_pourcentage", 0)
        except:
            return 0
    return 0

def format_nom_schema(nom_fichier):
    """Formate l'affichage dans la liste déroulante : Nom Propre + Score."""
    score = get_score(nom_fichier)
    # Nettoie le nom du fichier pour l'affichage (enlève .jpg, remplace les _ par des espaces)
    nom_propre = nom_fichier.replace('.jpg', '').replace('.png', '').replace('.jpeg', '').replace('_', ' ').title()
    
    if score > 0:
        return f"{nom_propre} - 🏆 {score}%"
    return f"{nom_propre} - ⚪ Nouveau"

# --- INITIALISATION MÉMOIRE ---
if 'schema_ready' not in st.session_state:
    st.session_state['schema_ready'] = False
    st.session_state['true_labels'] = []
if 'current_img_path' not in st.session_state:
    st.session_state['current_img_path'] = ""

# --- INTERFACE PRINCIPALE ---
st.title("🦴 Entraînement Ostéologie")
st.markdown("---")

# --- BARRE LATÉRALE (MENU) ---
with st.sidebar:
    st.header("📚 Bibliothèque")
    mode = st.radio("Mode :", ["📖 Ouvrir la banque", "➕ Ajouter un schéma"])
    
    image_a_traiter = None
    fichiers_banque = [f for f in os.listdir(BANQUE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if mode == "➕ Ajouter un schéma":
        st.subheader("Nouvel import")
        uploaded_file = st.file_uploader("Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_file:
            image_a_traiter = "temp_input.jpg"
            with open(image_a_traiter, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            nom_fichier = st.text_input("Nom du schéma (sans espace, utilise des '_' ex: crane_face) :")
            if st.button("💾 Sauvegarder dans la banque", use_container_width=True):
                if nom_fichier:
                    # Sécurise l'extension
                    if not nom_fichier.endswith('.jpg'):
                        nom_fichier += '.jpg'
                    chemin_sauvegarde = os.path.join(BANQUE_DIR, nom_fichier)
                    shutil.copy(image_a_traiter, chemin_sauvegarde)
                    st.success("Sauvegardé avec succès !")
                    st.rerun()
    else:
        if not fichiers_banque:
            st.info("La banque est vide. Ajoute un schéma d'abord.")
        else:
            image_choisie = st.selectbox(
                "Choisis ton exercice :", 
                fichiers_banque, 
                format_func=format_nom_schema
            )
            image_a_traiter = os.path.join(BANQUE_DIR, image_choisie)

# --- ZONE D'EXERCICE ---
if image_a_traiter:
    if st.session_state['current_img_path'] != image_a_traiter:
        st.session_state['schema_ready'] = False
        st.session_state['current_img_path'] = image_a_traiter

    # Modification des largeurs de colonnes (plus de place pour l'image sur grand écran)
    col_img, col_quiz = st.columns([1.2, 1])
    
    with col_img:
        st.subheader("🖼️ Le Schéma")
        with st.expander("👀 Voir le schéma original (Triche)"):
            st.image(image_a_traiter, use_container_width=True)
            
        if st.button("✨ Générer l'exercice", type="primary", use_container_width=True):
            with st.spinner("Analyse par l'IA en cours (cela prend quelques secondes)..."):
                st.session_state['true_labels'] = create_blind_schema(image_a_traiter, "temp_output.jpg")
                st.session_state['schema_ready'] = True
                st.rerun()
        
        if st.session_state['schema_ready']:
            st.image("temp_output.jpg", use_container_width=True)
            
    with col_quiz:
        if st.session_state['schema_ready']:
            st.subheader("📝 À toi de jouer !")
            labels = st.session_state['true_labels']
            
            # Utilisation du formulaire pour une ergonomie parfaite sur mobile
            with st.form("quiz_form"):
                for i in range(len(labels)):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.text_input(f"Légende n°{i+1}", key=f"rep_{i}")
                    with c2:
                        st.write("") 
                        st.checkbox("Ignorer 🗑️", key=f"ignore_{i}")
                        
                # Bouton de validation global
                submitted = st.form_submit_button("Vérifier mes réponses 🚀", use_container_width=True)
            
            # Correction affichée uniquement après clic sur le bouton du formulaire
            if submitted:
                st.markdown("### 📊 Résultats")
                score = 0
                questions_valides = 0
                
                for i, vrai_texte in enumerate(labels):
                    if st.session_state.get(f"ignore_{i}", False):
                        continue
                        
                    questions_valides += 1
                    reponse_user = st.session_state.get(f"rep_{i}", "").strip().lower()
                    vrai_texte_propre = vrai_texte.strip().lower()
                    
                    if reponse_user and (reponse_user in vrai_texte_propre or vrai_texte_propre in reponse_user):
                        st.success(f"**N°{i+1}.** ✅ {vrai_texte}")
                        score += 1
                    else:
                        st.error(f"**N°{i+1}.** ❌ Ta réponse: *{reponse_user if reponse_user else 'Vide'}* ➔ **Correction: {vrai_texte}**")
                
                # Gestion du score final
                if questions_valides > 0:
                    pourcentage = int((score / questions_valides) * 100)
                    
                    # Affichage graphique du score
                    col_score1, col_score2 = st.columns(2)
                    col_score1.metric("Score", f"{score} / {questions_valides}")
                    col_score2.metric("Précision", f"{pourcentage}%")
                    
                    nom_de_base = os.path.basename(image_a_traiter)
                    fichier_score = os.path.join(BANQUE_DIR, f"{nom_de_base}_score.json")
                    meilleur_pourcentage = get_score(nom_de_base)
                            
                    if pourcentage > meilleur_pourcentage:
                        with open(fichier_score, "w") as f:
                            json.dump({"meilleur_pourcentage": pourcentage}, f)
                        st.balloons()
                        st.success(f"Nouveau record ! Tu as battu l'ancien record de {meilleur_pourcentage}% 🏆")
                    else:
                        st.info(f"Record actuel à battre : {meilleur_pourcentage}%")
                else:
                    st.warning("Toutes les légendes ont été ignorées. Le score n'a pas pu être calculé.")
