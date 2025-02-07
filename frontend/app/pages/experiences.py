import streamlit as st


class Experience:
    def __init__(
        self,
        title: str,
        subtitle: str,
        date: str,
        context: str,
        missions: dict,
        realisations: list,
        picture: str,
    ):
        """
        Classe pour afficher une expérience sous forme d'une carte interactive dans Streamlit.

        Args:
            title (str): Titre de l'expérience.
            subtitle (str): Sous-titre.
            date (str): Date ou période.
            context (str): Contexte de l'expérience.
            missions (dict): Dictionnaire contenant un résumé et des exemples de missions.
            realisations (list): Liste des réalisations effectuées.
            picture (str): URL ou chemin de l'image associée.
        """
        self.title = title
        self.subtitle = subtitle
        self.date = date
        self.context = context
        self.missions = missions
        self.realisations = realisations  # Correction : "realisation" -> "realisations"
        self.picture = picture

    def display(self) -> None:
        """Affiche l'expérience sous forme de carte avec Streamlit."""
        with st.expander(label=f"**{self.title}**"):
            # En-tête
            col1, _, col2 = st.columns([2, 0.2, 1])
            col1.header(self.title)
            col2.header(self.date)
            st.subheader(f"_{self.subtitle}_")

            # Contexte
            col1, _, col2 = st.columns([2, 0.2, 1])
            col1.subheader("Contexte")
            col1.markdown(
                f'<div style="text-align: justify;">{self.context}</div>',
                unsafe_allow_html=True,
            )
            col2.image(self.picture, use_column_width=True)

            # Missions
            if self.missions and "examples" in self.missions:
                st.subheader("Missions")
                st.markdown(
                    f'<div style="text-align: justify;">{self.missions.get("resume", "")}</div>',
                    unsafe_allow_html=True,
                )

                col1, _, col2 = st.columns([1, 0.2, 1])
                for idx, (mission, description) in enumerate(
                    self.missions.get("examples", {}).items()
                ):
                    target_col = col1 if idx % 2 == 0 else col2
                    target_col.write(f"**_{mission}_**")
                    target_col.markdown(
                        f'<div style="text-align: justify;">{description}</div>',
                        unsafe_allow_html=True,
                    )

            # Réalisations
            st.subheader("Réalisations")
            for realization in self.realisations:
                st.write(f"• {realization}")


def experience_page(exp: dict) -> None:
    """Affiche la page des expériences avec tri par catégories."""
    st.header("EXPERIENCES")
    st.text("")

    # Affichage des images de catégories
    col1, col2, col3 = st.columns(3)
    col1.image("img/exp_data.jpg", width=200)
    col2.image("img/exp_chimie.jpg", width=200)
    col3.image("img/exp_open.jpg", width=200)

    st.markdown(
        "<h6 style='text-align: center; color: gray;'>Choisissez une catégorie</h6>",
        unsafe_allow_html=True,
    )

    # Création des onglets
    tab_data, tab_sciences, tab_diverses = st.tabs(
        ["Data", "Sciences", "Projets personnels"]
    )

    category_map = {"Data": tab_data, "Science": tab_sciences, "Diverses": tab_diverses}

    # Affichage des expériences dans les bonnes catégories
    for experience in exp.values():
        category = experience.get("type_exp")
        if category in category_map:
            with category_map[category]:
                Experience(**experience["body"]).display()
