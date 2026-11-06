"""Le coach IA : il aide l'étudiant à écrire son rapport sans l'écrire à sa place.

Deux fournisseurs d'IA sont possibles, choisis avec la variable INTERNLOG_IA :
- "gemini" (par défaut) : Google Gemini, avec une offre gratuite ;
- "claude" : l'API Claude d'Anthropic (payante).
"""

import os

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


class CoachError(Exception):
    """Erreur avec un message en français, prêt à afficher à l'étudiant."""

SYSTEM_PROMPT = """Tu es le tuteur d'écriture d'un étudiant qui rédige son rapport de stage.

Ton rôle est de l'aider à écrire lui-même, pas d'écrire à sa place :
- Tu ne rédiges jamais de paragraphe prêt à copier dans le rapport. Tu peux montrer une phrase d'exemple très courte pour illustrer un conseil de style, en disant clairement que c'est un exemple.
- Tu t'appuies uniquement sur le journal de stage et les documents fournis. Si une information manque, tu poses une question au lieu de l'inventer.
- Quand c'est utile, tu cites les semaines du journal concernées (par exemple « semaine 3 »).
- Tu ne donnes pas de note.
- Si l'étudiant te demande d'écrire la partie pour lui, tu refuses avec bienveillance et tu proposes des questions pour l'aider à avancer.

Tu réponds en français, simplement et avec des phrases complètes, comme un bon professeur encourageant."""

TASKS = {
    "questions": (
        "Pose 5 à 7 questions précises qui aideront l'étudiant à écrire cette partie. "
        "Chaque question doit partir de ce qu'il a noté dans son journal et pointer un détail à développer."
    ),
    "plan": (
        "Propose un plan pour cette partie : des titres et, sous chaque titre, 2 ou 3 idées clés en quelques mots, "
        "avec les semaines du journal à utiliser. Respecte la structure du modèle de l'école s'il est fourni. "
        "N'écris pas de paragraphes."
    ),
    "relecture": (
        "Relis le brouillon de l'étudiant et compare-le à la grille d'évaluation. Donne : "
        "1) ce qui est réussi, 2) les critères de la grille qui ne sont pas encore couverts, "
        "3) trois améliorations concrètes à faire, avec une question pour chacune. "
        "Ne réécris pas le brouillon."
    ),
}


def _format_journal(entries) -> str:
    if not entries:
        return "(Le journal est vide pour l'instant.)"
    blocks = []
    for e in entries:
        blocks.append(
            f"Semaine {e['numero_semaine']}\n"
            f"- Tâches : {e['taches']}\n"
            f"- Ce que j'ai appris : {e['apprentissages']}\n"
            f"- Difficultés : {e['difficultes']}"
        )
    return "\n\n".join(blocks)


def build_context(stage, entries, modele, grille) -> str:
    """Partie stable de la demande : elle change peu d'une demande à l'autre (mise en cache)."""
    parts = [
        "<stage>",
        f"Étudiant : {stage['etudiant']}\nEntreprise : {stage['entreprise']}\nPoste : {stage['poste']}\n"
        f"Du {stage['date_debut']} au {stage['date_fin']}",
        "</stage>",
        "<journal>", _format_journal(entries), "</journal>",
        "<modele_rapport>", modele or "(Pas de modèle déposé.)", "</modele_rapport>",
        "<grille_evaluation>", grille or "(Pas de grille déposée.)", "</grille_evaluation>",
    ]
    return "\n".join(parts)


def _ask_gemini(context: str, demande: str) -> str:
    from google import genai
    from google.genai import errors, types

    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        raise CoachError("Clé Gemini manquante. Ajoute GEMINI_API_KEY (voir le README).")
    client = genai.Client()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[context, demande],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=8192,
            ),
        )
    except errors.ClientError as err:
        if err.code == 429:
            raise CoachError("Limite gratuite atteinte pour le moment. Réessaie dans une minute.") from err
        if err.code in (400, 401, 403):
            raise CoachError("Clé Gemini invalide ou demande refusée. Vérifie GEMINI_API_KEY.") from err
        raise CoachError(f"Erreur de l'API Gemini ({err.code}).") from err
    except errors.ServerError as err:
        raise CoachError("Gemini est indisponible pour le moment. Réessaie dans un moment.") from err
    except Exception as err:  # le plus souvent : pas de connexion internet
        raise CoachError("Impossible de joindre Gemini. Vérifie ta connexion internet.") from err

    text = (response.text or "").strip()
    if not text:
        raise CoachError("Le coach n'a pas pu répondre à cette demande. Essaie de la reformuler.")
    return text


def _ask_claude(context: str, demande: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": context, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": demande},
                ],
            }],
        )
    except anthropic.AuthenticationError as err:
        raise CoachError("Clé API Claude manquante ou invalide. Vérifie ANTHROPIC_API_KEY.") from err
    except anthropic.APIConnectionError as err:
        raise CoachError("Impossible de joindre l'API Claude. Vérifie ta connexion internet.") from err
    except anthropic.APIStatusError as err:
        raise CoachError(f"Erreur de l'API Claude ({err.status_code}). Réessaie dans un moment.") from err

    if response.stop_reason == "refusal":
        raise CoachError("Le coach n'a pas pu répondre à cette demande. Essaie de la reformuler.")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if response.stop_reason == "max_tokens":
        text += "\n\n(Réponse coupée : elle était trop longue.)"
    return text


PROVIDERS = {"gemini": _ask_gemini, "claude": _ask_claude}


def ask_coach(type_demande: str, context: str, section_titre: str, brouillon: str) -> str:
    if type_demande not in TASKS:
        raise ValueError(f"Type de demande inconnu : {type_demande}")
    provider = os.environ.get("INTERNLOG_IA", "gemini").lower()
    if provider not in PROVIDERS:
        raise CoachError(f"INTERNLOG_IA doit valoir « gemini » ou « claude », pas « {provider} ».")

    demande = (
        f"Partie du rapport : « {section_titre} »\n\n"
        f"<brouillon>\n{brouillon or '(Pas encore de brouillon.)'}\n</brouillon>\n\n"
        f"Consigne : {TASKS[type_demande]}"
    )
    return PROVIDERS[provider](context, demande)
