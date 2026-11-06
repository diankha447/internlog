# InternLog : conception de la première version

InternLog suit le stage d'un étudiant semaine après semaine, puis l'aide à écrire son rapport **sans l'écrire à sa place**.

Cette version 1 concerne un seul utilisateur (l'étudiant) et tourne sur son ordinateur.

---

## 1. Diagramme de cas d'utilisation

Ce diagramme répond à la question : **qui fait quoi avec l'application ?**

```mermaid
flowchart LR
    E((Étudiant))
    IA((IA coach<br/>Claude))

    subgraph App[Application InternLog]
        UC1([Renseigner mon stage])
        UC2([Écrire le journal de la semaine])
        UC3([Consulter mes semaines])
        UC4([Déposer le modèle de rapport])
        UC5([Déposer la grille d'évaluation])
        UC6([Écrire une partie du rapport])
        UC7([Demander des questions pour m'aider])
        UC8([Demander un plan pour une partie])
        UC9([Faire relire mon brouillon selon la grille])
    end

    E --> UC1
    E --> UC2
    E --> UC3
    E --> UC4
    E --> UC5
    E --> UC6
    UC6 -.inclut.-> UC7
    UC6 -.inclut.-> UC8
    UC6 -.inclut.-> UC9
    UC7 --> IA
    UC8 --> IA
    UC9 --> IA
```

En résumé :
- L'**étudiant** est l'acteur principal. Il fait tout dans l'application.
- L'**IA** est un acteur secondaire. Elle intervient seulement quand l'étudiant écrit son rapport, et elle répond à trois types de demande : des questions, un plan, une relecture.

---

## 2. Diagramme de classes (le modèle de données)

Ce diagramme répond à la question : **quelles informations l'application garde-t-elle, et comment sont-elles liées ?**

```mermaid
classDiagram
    class Stage {
        +int id
        +str etudiant
        +str entreprise
        +str poste
        +date date_debut
        +date date_fin
    }

    class EntreeJournal {
        +int id
        +int numero_semaine
        +str taches
        +str apprentissages
        +str difficultes
        +date cree_le
    }

    class Document {
        +int id
        +str type
        +str nom_fichier
        +str texte_extrait
        +date depose_le
    }

    class SectionRapport {
        +int id
        +str titre
        +str brouillon
        +date modifie_le
    }

    class EchangeIA {
        +int id
        +str type_demande
        +str reponse
        +date cree_le
    }

    Stage "1" --> "*" EntreeJournal : contient
    Stage "1" --> "0..2" Document : possède
    Stage "1" --> "*" SectionRapport : rapport
    SectionRapport "1" --> "*" EchangeIA : historique
```

Ce qu'il faut retenir :
- Tout est rattaché à un **Stage**.
- Une **EntreeJournal** correspond à une semaine (3 champs courts, environ 2 minutes à remplir).
- Un **Document** (champ `type` : `modele` ou `grille`) est soit le modèle de rapport de l'école, soit la grille d'évaluation. On garde le texte extrait du fichier pour l'envoyer à l'IA.
- Une **SectionRapport** est une partie du rapport (par exemple « Présentation de l'entreprise »). C'est l'étudiant qui écrit le brouillon.
- Un **EchangeIA** (champ `type_demande` : `questions`, `plan` ou `relecture`) garde chaque réponse de l'IA pour pouvoir la relire plus tard.

---

## 3. Les règles de l'IA

L'IA joue le rôle d'un **tuteur**, pas celui d'un rédacteur. Ces règles se trouvent dans le prompt système (`internlog/coach.py`).

| L'IA peut | L'IA ne doit pas |
|---|---|
| Poser des questions qui s'appuient sur le journal | Rédiger des paragraphes prêts à copier |
| Proposer un plan sous forme de titres et de points clés | Inventer des faits absents du journal |
| Comparer le brouillon à la grille et dire ce qui manque | Donner une note |
| Citer les semaines du journal à utiliser | Réécrire le brouillon de l'étudiant |

Si l'étudiant demande « écris-le pour moi », l'IA refuse poliment et propose de l'aider avec des questions.

---

## 4. Architecture technique (simple)

```mermaid
flowchart LR
    UI[Interface Streamlit<br/>app.py] --> DB[(SQLite<br/>internlog.db)]
    UI --> DOC[Lecture PDF / Word<br/>documents.py]
    UI --> COACH[Coach IA<br/>coach.py]
    COACH --> API[API Claude]
```

- **Python + Streamlit** pour l'interface : une page web sans HTML à écrire.
- **SQLite** pour les données : un seul fichier, aucune installation.
- **pypdf / python-docx** pour lire le modèle et la grille.
- **API Claude** pour le coach.

---

## 5. Hors de la version 1 (pour plus tard)

- Préparation de la soutenance (questions du jury, entraînement à l'oral)
- Comptes multiples, accès du tuteur ou de l'école
- Rappels automatiques chaque semaine
- Export du rapport en Word
