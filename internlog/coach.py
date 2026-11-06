"""Le coach IA : il aide l'étudiant à écrire son rapport sans l'écrire à sa place."""

import anthropic

MODEL = "claude-opus-5-5"

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


def ask_coach(type_demande: str, context: str, section_titre: str, brouillon: str,
              client: anthropic.Anthropic | None = None) -> str:
    if type_demande not in TASKS:
        raise ValueError(f"Type de demande inconnu : {type_demande}")
    client = client or anthropic.Anthropic()

    demande = (
        f"Partie du rapport : « {section_titre} »\n\n"
        f"<brouillon>\n{brouillon or '(Pas encore de brouillon.)'}\n</brouillon>\n\n"
        f"Consigne : {TASKS[type_demande]}"
    )

    response = client.beta.messages.create(
        model=MODEL,
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

    if response.stop_reason == "refusal":
        return "Le coach n'a pas pu répondre à cette demande. Essaie de la reformuler."
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if response.stop_reason == "max_tokens":
        text += "\n\n(Réponse coupée : elle était trop longue.)"
    return text
