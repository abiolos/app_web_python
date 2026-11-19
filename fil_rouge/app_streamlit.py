
import pandas as pd
import plotly.express as px
import streamlit as st

from data import load_coups, load_data

# Configuration de la page
st.set_page_config(
    page_title="Que dois-je travailler aux échecs ?",
    page_icon="♟️",
    layout="wide"
)

# 1. Chargement des données
@st.cache_data
def charger_donnees():
    return load_data(), load_coups()


df, coups = charger_donnees()

# Vérifier les formats
df["date_jeu"] = pd.to_datetime(df["date_jeu"])
df["cadence"] = df["cadence"].fillna("aucune")

# 2. Titre
st.title("♟️ Je stagne aux échecs : que devrais-je travailler ?")
st.write(
    "Analyse de mes parties pour identifier "
    "les points à améliorer."
)

# 3. Barre latérale
st.sidebar.header("Filtres")

# Filtre multisélection : cadence
cadences = sorted(df["cadence"].unique().tolist())

cadence = st.sidebar.multiselect(
    "Sélectionner les cadences",
    options=cadences,
    default=cadences,
    key="filtre_cadence"
)

# Filtre période
periode = st.sidebar.date_input(
    "Sélectionner la période",
    value=(
        df["date_jeu"].min().date(),
        df["date_jeu"].max().date()
    ),
    min_value=df["date_jeu"].min().date(),
    max_value=df["date_jeu"].max().date(),
    key="filtre_periode"
)

# Filtre multisélection : couleur
couleurs = ["white", "black"]

couleur = st.sidebar.multiselect(
    "Sélectionner les couleurs",
    options=couleurs,
    default=couleurs,
    format_func=lambda x: {
        "white": "Blancs",
        "black": "Noirs"
    }[x],
    key="filtre_couleur"
)

# 4. Filtrage des données
if len(periode) != 2:
    st.info("Sélectionnez une date de début et une date de fin.")
    st.stop()

debut, fin = periode

vue = df[
    df["cadence"].isin(cadence)
    & df["couleur"].isin(couleur)
    & (df["date_jeu"].dt.date >= debut)
    & (df["date_jeu"].dt.date <= fin)
].copy()

# Message si aucun résultat
if vue.empty:
    st.warning(
        "Aucune partie ne correspond aux filtres sélectionnés."
    )
    st.stop()

# 5. Indicateurs
st.subheader("Mes statistiques")

nombre_parties = len(vue)
score_moyen = vue["score"].mean()
gaffes_moyennes = vue["gaffes_joueur"].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Parties jouées",
        value=nombre_parties
    )

with col2:
    st.metric(
        label="Score moyen",
        value=f"{score_moyen:.1%}"
    )

with col3:
    st.metric(
        label="Gaffes par partie",
        value=f"{gaffes_moyennes:.2f}"
    )

st.divider()

# 6. Graphiques
st.subheader("Analyse des performances")

col_gauche, col_droite = st.columns(2)

# Graphique 1 : Score par famille d'ouvertures
with col_gauche:

    stats_ouvertures = (
        vue.groupby("ouverture_famille")
        .agg(
            n=("partie_id", "count"),
            score=("score", "mean"),
            gaffes=("gaffes_joueur", "mean")
        )
        .reset_index()
        .rename(columns={
            "ouverture_famille": "famille"
        })
    )

    # Garder les familles avec au moins 30 parties
    stats_ouvertures = stats_ouvertures[
        stats_ouvertures["n"] >= 30
    ].sort_values("score")

    if stats_ouvertures.empty:
        st.info(
            "Pas assez de parties pour analyser les ouvertures."
        )
    else:
        fig1 = px.bar(
            stats_ouvertures,
            x="score",
            y="famille",
            orientation="h",
            color="score",
            color_continuous_scale="RdYlGn",
            title="Score par famille d'ouvertures",
            labels={
                "score": "Score moyen",
                "famille": "Ouverture"
            },
            hover_data=["n", "gaffes"]
        )

        fig1.update_layout(
            yaxis={
                "categoryorder": "array",
                "categoryarray": stats_ouvertures[
                    "famille"
                ].iloc[::-1].tolist()
            },
            coloraxis_showscale=False
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

# Graphique 2 : Gaffes par phase
with col_droite:

    # Garder uniquement les coups des parties filtrées
    coups_filtres = coups[
        coups["partie_id"].isin(vue["partie_id"])
    ].copy()

    # Garder uniquement les gaffes
    gaffes = coups_filtres[
        coups_filtres["jugement"] == "blunder"
    ]

    phases = ["opening", "middlegame", "endgame"]

    stats_phases = (
        gaffes["phase"]
        .value_counts()
        .reindex(phases, fill_value=0)
        .reset_index()
    )

    stats_phases.columns = ["phase", "nombre"]

    stats_phases["phase"] = stats_phases["phase"].map({
        "opening": "Ouverture",
        "middlegame": "Milieu de partie",
        "endgame": "Finale"
    })

    fig2 = px.bar(
        stats_phases,
        x="phase",
        y="nombre",
        color="phase",
        title="Dans quelle phase fais-je le plus de gaffes ?",
        labels={
            "phase": "Phase de la partie",
            "nombre": "Nombre de gaffes"
        },
        text="nombre"
    )

    fig2.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# 7. Tableau des parties filtrées
st.divider()

st.subheader("Détail des parties sélectionnées")

st.dataframe(
    vue,
    use_container_width=True
)

st.caption(
    f"{len(vue)} parties affichées sur {len(df)} au total."
)

print("relance")
