"""InternLog : interface Streamlit. Lancer avec : streamlit run app.py"""

import datetime as dt

import streamlit as st

from internlog import coach, db
from internlog.documents import extract_text

st.set_page_config(page_title="InternLog", page_icon="📓", layout="wide")
db.init()

st.title("📓 InternLog")
st.caption("Le journal de ton stage, et un coach pour écrire ton rapport toi-même.")

# ---------- Mon stage ----------
with db.connect() as c:
    stage = db.get_stage(c)

with st.sidebar:
    st.header("Mon stage")
    with st.form("stage"):
        etudiant = st.text_input("Mon nom", stage["etudiant"] if stage else "")
        entreprise = st.text_input("Entreprise", stage["entreprise"] if stage else "")
        poste = st.text_input("Poste / missions", stage["poste"] if stage else "")
        debut = st.date_input(
            "Début",
            dt.date.fromisoformat(stage["date_debut"]) if stage else dt.date.today(),
        )
        fin = st.date_input(
            "Fin",
            dt.date.fromisoformat(stage["date_fin"])
            if stage else dt.date.today() + dt.timedelta(weeks=12),
        )
        if st.form_submit_button("Enregistrer"):
            with db.connect() as c:
                db.save_stage(c, etudiant, entreprise, poste, debut, fin)
            st.rerun()

if not stage:
    st.info("Commence par renseigner ton stage dans la colonne de gauche.")
    st.stop()

stage_id = stage["id"]
debut_stage = dt.date.fromisoformat(stage["date_debut"])
semaine_actuelle = max(1, (dt.date.today() - debut_stage).days // 7 + 1)

tab_journal, tab_docs, tab_rapport = st.tabs(
    ["🗓️ Journal de la semaine", "📎 Modèle et grille", "✍️ Mon rapport"]
)

# ---------- Journal ----------
with tab_journal:
    with db.connect() as c:
        entries = db.list_entries(c, stage_id)
    existantes = {e["numero_semaine"]: e for e in entries}

    st.subheader("Ma semaine en 2 minutes")
    semaine = st.number_input("Semaine n°", min_value=1, value=semaine_actuelle, step=1)
    e = existantes.get(semaine)
    with st.form("journal", clear_on_submit=False):
        taches = st.text_area("Qu'est-ce que j'ai fait cette semaine ?", e["taches"] if e else "")
        apprentissages = st.text_area("Qu'est-ce que j'ai appris ?", e["apprentissages"] if e else "")
        difficultes = st.text_area(
            "Une difficulté, et comment je l'ai gérée ?", e["difficultes"] if e else ""
        )
        if st.form_submit_button("Enregistrer ma semaine"):
            with db.connect() as c:
                db.save_entry(c, stage_id, semaine, taches, apprentissages, difficultes)
            st.success(f"Semaine {semaine} enregistrée.")
            st.rerun()

    st.subheader("Mes semaines")
    if not entries:
        st.write("Aucune semaine pour l'instant.")
    for e in reversed(entries):
        with st.expander(f"Semaine {e['numero_semaine']}"):
            st.markdown(f"**Tâches :** {e['taches']}")
            st.markdown(f"**Appris :** {e['apprentissages']}")
            st.markdown(f"**Difficultés :** {e['difficultes']}")

# ---------- Documents ----------
with tab_docs:
    st.write("Dépose les documents de ton école. Le coach s'en sert pour te guider.")
    for type_, label in [("modele", "Modèle de rapport"), ("grille", "Grille d'évaluation")]:
        st.subheader(label)
        with db.connect() as c:
            doc = db.get_document(c, stage_id, type_)
        if doc:
            st.caption(f"Fichier actuel : {doc['nom_fichier']}")
            with st.expander("Voir le texte lu"):
                st.text(doc["texte_extrait"][:5000])
        fichier = st.file_uploader(
            f"Déposer le {label.lower()}", type=["pdf", "docx", "txt", "md"], key=type_
        )
        if fichier and st.button(f"Enregistrer le {label.lower()}", key=f"save_{type_}"):
            try:
                texte = extract_text(fichier.name, fichier.getvalue())
            except Exception as err:  # fichier illisible ou mauvais format
                st.error(f"Impossible de lire ce fichier : {err}")
            else:
                if not texte:
                    st.warning("Aucun texte trouvé. Le fichier est peut-être une image scannée.")
                with db.connect() as c:
                    db.save_document(c, stage_id, type_, fichier.name, texte)
                st.success("Document enregistré.")
                st.rerun()

# ---------- Rapport ----------
with tab_rapport:
    with db.connect() as c:
        sections = db.list_sections(c, stage_id)

    with st.form("nouvelle_section", clear_on_submit=True):
        titre = st.text_input("Ajouter une partie du rapport (ex. « Présentation de l'entreprise »)")
        if st.form_submit_button("Ajouter") and titre.strip():
            with db.connect() as c:
                db.add_section(c, stage_id, titre.strip())
            st.rerun()

    if not sections:
        st.info("Ajoute une première partie de ton rapport pour commencer.")
        st.stop()

    choix = st.selectbox("Partie", sections, format_func=lambda s: s["titre"])
    brouillon = st.text_area("Mon brouillon", choix["brouillon"], height=300, key=f"b{choix['id']}")
    if st.button("Enregistrer le brouillon"):
        with db.connect() as c:
            db.save_draft(c, choix["id"], brouillon)
        st.success("Brouillon enregistré.")

    st.markdown("**Demander de l'aide au coach**")
    col1, col2, col3 = st.columns(3)
    demande = None
    if col1.button("❓ Des questions pour m'aider"):
        demande = "questions"
    if col2.button("🧭 Un plan pour cette partie"):
        demande = "plan"
    if col3.button("🔍 Relire selon la grille"):
        demande = "relecture"

    if demande:
        with db.connect() as c:
            db.save_draft(c, choix["id"], brouillon)
            modele = db.get_document(c, stage_id, "modele")
            grille = db.get_document(c, stage_id, "grille")
            entries = db.list_entries(c, stage_id)
        contexte = coach.build_context(
            stage, entries,
            modele["texte_extrait"] if modele else None,
            grille["texte_extrait"] if grille else None,
        )
        with st.spinner("Le coach réfléchit..."):
            try:
                reponse = coach.ask_coach(demande, contexte, choix["titre"], brouillon)
            except coach.CoachError as err:
                st.error(str(err))
                st.stop()
        with db.connect() as c:
            db.save_exchange(c, choix["id"], demande, reponse)

    with db.connect() as c:
        historique = db.list_exchanges(c, choix["id"])
    labels = {"questions": "Questions", "plan": "Plan", "relecture": "Relecture"}
    for i, ex in enumerate(historique):
        with st.expander(f"{labels.get(ex['type_demande'], ex['type_demande'])} · {ex['cree_le']}",
                         expanded=(i == 0)):
            st.markdown(ex["reponse"])
