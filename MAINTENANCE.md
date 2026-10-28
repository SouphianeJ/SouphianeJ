# Maintenance du profil

Le README affiche une seule composition SVG : les sections restent jointives sur GitHub. Une version sans animation suit la préférence `prefers-reduced-motion` et le texte complet reste disponible dans le volet dépliable.

## Sources et génération

| Source | Rôle |
| --- | --- |
| `content/profile.md` | Texte éditorial ; `{{impact_summary}}` insère le cas concret. |
| `content/impact.json` | Agrégats du cas intervenants fournis par le propriétaire, pour les deux premiers mois de production. Les catégories sont partielles. |
| `assets/astronaut.svg` et `assets/astronaut-static.svg` | Illustration pixel art de référence et séquence validée. |
| `profile_design/` | Lecture des données, primitives SVG, sprites, calendrier et composition. |
| `assets/activity.json` | Dernier relevé GitHub agrégé : période, dates et compteurs uniquement. |
| `assets/activity.svg`, `assets/profile.svg`, `assets/profile-static.svg`, `README.md` | Fichiers générés, à ne pas éditer directement. |

Python **3.12 ou ultérieur** suffit à l’exécution ; le générateur utilise uniquement la bibliothèque standard. Les sprites de jeu et les icônes sont construits par le code. Les scènes décoratives ne modifient aucune donnée du calendrier.

```bash
python3 -m profile_design.build
python3 -m profile_design.build --check
python3 -m unittest discover -s tests -v
```

Pour la relecture du code :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

## Actualisation GitHub

Le workflow vérifie style, tests et reproductibilité sur les changements de source et les pull requests. L’actualisation réseau et le push sont réservés à `main` dans `SouphianeJ/SouphianeJ`, après validation, à **05:23 et 17:23 UTC**, sur changement de source ou sur déclenchement manuel. GitHub peut retarder les tâches planifiées. Le job de contrôle est en lecture seule, sans conservation d’identifiants Git ; seul le job de publication reçoit `contents: write`. L’action checkout est épinglée à un SHA.

La lecture GraphQL utilise le `GITHUB_TOKEN` automatique. Les contributions privées déjà partagées anonymement sur le profil sont incluses sans accès à leur contenu. `restrictedContributionsCount` décrit les contributions dont les détails ne sont pas accessibles au jeton observateur ; ce compteur n’est pas ajouté une deuxième fois au total du calendrier. Les règles de comptage sont celles de GitHub, pas une mesure du temps de travail ou de la qualité du code.

Pour une actualisation locale, fournir `GITHUB_TOKEN` ou `GH_TOKEN` via l’environnement ou un gestionnaire de secrets, puis lancer :

```bash
python3 -m profile_design.build --refresh
```

Aucun jeton personnel n’est nécessaire au workflow ni enregistré dans le dépôt. Une réponse API invalide ou un calendrier incomplet fait échouer le job avant tout commit : les visuels publiés sont conservés. Si les faits sont inchangés, l’horodatage du relevé précédent est conservé pour éviter les commits dus au seul passage du temps. Le push ne concerne que les cinq fichiers générés annoncés dans le workflow et n’utilise jamais de force push.

## Publication

Regénérer les fichiers avant de committer une modification éditoriale ou graphique. Vérifier le workflow sur le commit publié, puis le rendu sur le profil : l’apparence et le cache d’images de GitHub ne sont pas entièrement reproduits par les contrôles XML. Les intitulés de projets et les chiffres d’usage proviennent du propriétaire ; le calendrier est le seul bloc alimenté directement par GitHub.
