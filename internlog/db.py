"""Stockage SQLite : un seul fichier, aucune installation."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "internlog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stage (
    id INTEGER PRIMARY KEY,
    etudiant TEXT, entreprise TEXT, poste TEXT,
    date_debut TEXT, date_fin TEXT
);
CREATE TABLE IF NOT EXISTS entree_journal (
    id INTEGER PRIMARY KEY,
    stage_id INTEGER NOT NULL REFERENCES stage(id),
    numero_semaine INTEGER NOT NULL,
    taches TEXT, apprentissages TEXT, difficultes TEXT,
    cree_le TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (stage_id, numero_semaine)
);
CREATE TABLE IF NOT EXISTS document (
    id INTEGER PRIMARY KEY,
    stage_id INTEGER NOT NULL REFERENCES stage(id),
    type TEXT NOT NULL CHECK (type IN ('modele', 'grille')),
    nom_fichier TEXT, texte_extrait TEXT,
    depose_le TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (stage_id, type)
);
CREATE TABLE IF NOT EXISTS section_rapport (
    id INTEGER PRIMARY KEY,
    stage_id INTEGER NOT NULL REFERENCES stage(id),
    titre TEXT NOT NULL, brouillon TEXT DEFAULT '',
    modifie_le TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS echange_ia (
    id INTEGER PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES section_rapport(id),
    type_demande TEXT NOT NULL, reponse TEXT,
    cree_le TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def connect(path: Path = DB_PATH):
    conn = sqlite3.connect(path)
    # Des dictionnaires simples, faciles à manipuler dans Streamlit
    conn.row_factory = lambda cur, row: {col[0]: row[i] for i, col in enumerate(cur.description)}
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init(path: Path = DB_PATH) -> None:
    with connect(path) as c:
        c.executescript(SCHEMA)


# --- Stage (un seul stage dans la version 1) ---

def get_stage(c):
    return c.execute("SELECT * FROM stage ORDER BY id LIMIT 1").fetchone()


def save_stage(c, etudiant, entreprise, poste, date_debut, date_fin) -> int:
    s = get_stage(c)
    vals = (etudiant, entreprise, poste, str(date_debut), str(date_fin))
    if s:
        c.execute(
            "UPDATE stage SET etudiant=?, entreprise=?, poste=?, date_debut=?, date_fin=? WHERE id=?",
            (*vals, s["id"]),
        )
        return s["id"]
    return c.execute(
        "INSERT INTO stage (etudiant, entreprise, poste, date_debut, date_fin) VALUES (?,?,?,?,?)",
        vals,
    ).lastrowid


# --- Journal ---

def save_entry(c, stage_id, semaine, taches, apprentissages, difficultes) -> None:
    c.execute(
        """INSERT INTO entree_journal (stage_id, numero_semaine, taches, apprentissages, difficultes)
           VALUES (?,?,?,?,?)
           ON CONFLICT(stage_id, numero_semaine) DO UPDATE SET
             taches=excluded.taches, apprentissages=excluded.apprentissages,
             difficultes=excluded.difficultes""",
        (stage_id, semaine, taches, apprentissages, difficultes),
    )


def list_entries(c, stage_id):
    return c.execute(
        "SELECT * FROM entree_journal WHERE stage_id=? ORDER BY numero_semaine", (stage_id,)
    ).fetchall()


# --- Documents (modèle et grille) ---

def save_document(c, stage_id, type_, nom_fichier, texte) -> None:
    c.execute(
        """INSERT INTO document (stage_id, type, nom_fichier, texte_extrait) VALUES (?,?,?,?)
           ON CONFLICT(stage_id, type) DO UPDATE SET
             nom_fichier=excluded.nom_fichier, texte_extrait=excluded.texte_extrait,
             depose_le=CURRENT_TIMESTAMP""",
        (stage_id, type_, nom_fichier, texte),
    )


def get_document(c, stage_id, type_):
    return c.execute(
        "SELECT * FROM document WHERE stage_id=? AND type=?", (stage_id, type_)
    ).fetchone()


# --- Sections du rapport ---

def add_section(c, stage_id, titre) -> int:
    return c.execute(
        "INSERT INTO section_rapport (stage_id, titre) VALUES (?,?)", (stage_id, titre)
    ).lastrowid


def list_sections(c, stage_id):
    return c.execute(
        "SELECT * FROM section_rapport WHERE stage_id=? ORDER BY id", (stage_id,)
    ).fetchall()


def save_draft(c, section_id, brouillon) -> None:
    c.execute(
        "UPDATE section_rapport SET brouillon=?, modifie_le=CURRENT_TIMESTAMP WHERE id=?",
        (brouillon, section_id),
    )


# --- Historique IA ---

def save_exchange(c, section_id, type_demande, reponse) -> None:
    c.execute(
        "INSERT INTO echange_ia (section_id, type_demande, reponse) VALUES (?,?,?)",
        (section_id, type_demande, reponse),
    )


def list_exchanges(c, section_id):
    return c.execute(
        "SELECT * FROM echange_ia WHERE section_id=? ORDER BY id DESC", (section_id,)
    ).fetchall()
