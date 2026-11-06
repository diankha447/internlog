# InternLog

Une application qui suit ton stage semaine après semaine, puis t'aide à écrire ton rapport **sans l'écrire à ta place**.

- 🗓️ **Journal de la semaine** : 3 questions, environ 2 minutes.
- 📎 **Modèle et grille** : tu déposes le modèle de rapport et la grille d'évaluation de ton école (PDF ou Word).
- ✍️ **Mon rapport** : tu écris chaque partie toi-même, et le coach IA te pose des questions, propose un plan ou relit ton brouillon selon la grille.

La conception (diagrammes UML) se trouve dans [docs/conception.md](docs/conception.md).

## Lancer l'application

1. Installe Python 3.10 ou plus récent.
2. Dans un terminal, depuis ce dossier :
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows : .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Récupère une clé Gemini gratuite :
   - Va sur https://aistudio.google.com/apikey et connecte-toi avec ton compte Google.
   - Clique sur « Create API key » (Créer une clé API), puis copie la clé.
   - Dans le terminal :
   ```bash
   export GEMINI_API_KEY="ta-clé"     # Windows : set GEMINI_API_KEY=ta-clé
   ```
   Ne mets jamais cette clé dans un fichier envoyé sur GitHub.
4. Lance :
   ```bash
   streamlit run app.py
   ```
   La page s'ouvre dans ton navigateur.

Les données sont enregistrées dans le fichier `internlog.db`, à côté de l'application.

## Changer d'IA

Par défaut, le coach utilise **Google Gemini** (offre gratuite, avec un nombre limité de demandes par minute et par jour). Si la limite est atteinte, l'application te demande d'attendre un peu.

Attention : avec l'offre gratuite, Google peut utiliser ce que tu envoies pour améliorer ses produits. Évite d'écrire des informations confidentielles de l'entreprise dans le journal.

Pour utiliser Claude à la place (payant) :
```bash
export INTERNLOG_IA=claude
export ANTHROPIC_API_KEY="ta-clé"
```

Tu peux aussi choisir un autre modèle Gemini avec `GEMINI_MODEL` (par défaut : `gemini-flash-latest`).
