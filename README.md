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
3. Ajoute ta clé API Claude (à créer sur https://platform.claude.com) :
   ```bash
   export ANTHROPIC_API_KEY="ta-clé"     # Windows : set ANTHROPIC_API_KEY=ta-clé
   ```
4. Lance :
   ```bash
   streamlit run app.py
   ```
   La page s'ouvre dans ton navigateur.

Les données sont enregistrées dans le fichier `internlog.db`, à côté de l'application.
