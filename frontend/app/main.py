import os
import base64
from pathlib import Path
import streamlit as st
import requests
from settings import settings


BASE_DIR = str(Path(__file__).resolve().parent)
API_URL_CHAT = "http://localhost:8088/chatting/chat"
API_URL_EMBEDDING = "http://localhost:8088/embeddings/embedded"
API_URL_SUM = "http://localhost:8088/chatting/summary"
# API_URL_CHAT = "http://localhost/api/chatting/chat"
# API_URL_EMBEDDING = "http://localhost/api/embeddings/embedded"
# API_URL_SUM = "http://localhost/api/chatting/summary"

st.set_page_config(
    page_title="CV_JBDENIS",
    page_icon="🧊",
)

# Helper functions for background


def get_base64_of_bin_file(bin_file):  # noqa: ANN001, ANN201, D103
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_png_as_page_bg(png_file) -> None:  # noqa: ANN001, D103
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = (
        """
            <style>
            .stApp {
            background-image: url("data:image/png;base64,%s");
            background-size: cover;
            }
            </style>
        """  # noqa: UP031
        % bin_str
    )
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return  # noqa: PLR1711


# Set background
set_png_as_page_bg(png_file=r"app\resources\aide-financiere-ademe.jpg")

logo_path = r"app\resources\logo_ademe.png"

col1, col2 = st.columns([3, 2])
with col1:
    st.image(logo_path, width=400)
with col2:
    st.title("Dis-ADEME")
    st.write("Bienvenue dans votre application de chat.")

# Navigation
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ["Accueil", "Admin"])


def save_uploaded_files(uploaded_files: list):  # noqa: ANN201, D103
    save_dir = BASE_DIR + r"\uploaded_files\user"
    # save_dir = r"\Shared_data\uploaded_files"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    saved_file_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_file_paths.append(file_path)
        st.session_state.uploaded_files.append(file_path)

    return saved_file_paths


# Page d'accueil
if page == "Accueil":
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    saved_paths = []
    with st.sidebar:
        st.header("Uploader des fichiers PDF")
        uploaded_files = st.file_uploader(
            "Choisissez des fichiers PDF",
            type="pdf",
            accept_multiple_files=True,
            key="pdf_uploader",
        )

        if uploaded_files:
            saved_paths = save_uploaded_files(uploaded_files)
            st.success(f"Fichiers sauvegardés : {saved_paths[-1]}, en analyse ...")

        if saved_paths:
            try:
                response = requests.post(
                    API_URL_EMBEDDING,
                    json={"doc_paths": saved_paths[-1], "vectorstor_type": "user"},
                )
                response.raise_for_status()
                embedded = response.json().get(
                    "message",
                    "Désolé, une erreur s'est produite durant la lecture du fichier.",
                )

                if response:
                    st.success(f"Analyse du fichiers {saved_paths[-1]} terminée.")

                saved_paths = []
            except requests.RequestException as e:
                embedded = f"Erreur lors de la communication avec l'API : {e}"

        if st.session_state.messages:
            st.write("")
            st.divider()
            st.write("")
            st.header("Rapport de conversation")
            if st.button("Générer le rapport de conversation"):
                try:
                    response = requests.post(
                        API_URL_SUM, json={"messages": st.session_state.messages}
                    )
                    response.raise_for_status()
                    summary = response.json().get("summary", "Résumé non disponible.")
                    st.subheader("Résumé généré")
                    st.text_area("Rapport", summary, height=200)
                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur lors de l'appel de l'API : {e}")
                if response:
                    with open(r"..\Shared_data\export.pdf", "rb") as pdf_file:
                        # with open(r"C:\Users\jeanb\Documents\kzs-team\Shared_data\export.pdf", "rb") as pdf_file:

                        PDFbyte = pdf_file.read()

                    if PDFbyte:
                        st.download_button(
                            label="Télécharger le rapport de conversation",
                            data=PDFbyte,
                            file_name="Conversation_Dis_ADEME.pdf",
                            mime="application/octet-stream",
                        )

    # Chatbot
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message["avatar"]):
            st.write(message["content"])

    if prompt := st.chat_input("Comment puis-je vous aider ?"):
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "avatar": "👤"}
        )
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)

        try:
            response = requests.post(API_URL_CHAT, json={"user_query": prompt})
            response.raise_for_status()
            data = response.json()
            answer = data.get(
                "formatted_output", "Désolé, je n'ai pas de réponse à cette question."
            )
        except requests.RequestException as e:
            answer = f"Erreur lors de la communication avec l'API : {e}"

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "avatar": "🤖"}
        )
        with st.chat_message("assistant", avatar="🤖"):
            st.write(answer)

# Page Admin
elif page == "Admin":
    st.title("Admin - Ajouter des documents à la base de données")

    doc_path = st.text_input("Entrez le chemin du document ou du dossier à ajouter")

    if st.button("Ajouter les documents PDF à la base de données"):
        if doc_path:
            print("SAVED DOC:", doc_path)
            try:
                response = requests.post(
                    API_URL_EMBEDDING,
                    json={"doc_paths": doc_path, "vectorstor_type": "doc"},
                )
                response.raise_for_status()
                st.success("Documents ajoutés à la base de données avec succès.")
            except requests.RequestException as e:
                st.error(f"Erreur lors de l'ajout des documents : {e}")
        else:
            st.warning("Veuillez entrer un chemin valide.")
