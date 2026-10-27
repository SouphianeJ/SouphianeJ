# Maintenance du profil

Le README et les illustrations sont destinés au profil GitHub de SouphianeJ.

## Bandeau

Modifier `scripts/compose_profile.py`, puis lancer `python3 scripts/compose_profile.py`. Les sources de l’illustration animée et sa version statique sont dans `assets/astronaut.svg` et `assets/astronaut-static.svg`. L’animation est autonome, sans JavaScript ni service externe. Le README utilise un `picture` pour sélectionner le bandeau statique lorsque le système demande de réduire les animations.

## Calendrier de contributions

Le workflow `.github/workflows/update-activity.yml` actualise le calendrier à 05:23 et 17:23 UTC, avec déclenchement manuel possible. Il lit les agrégats via le jeton automatique GITHUB_TOKEN, sans demander de secret personnel. Le partage anonyme des contributions privées doit rester activé sur le profil pour qu’elles soient visibles à ce jeton.

Les contributions anonymisées ne sont pas ajoutées une seconde fois au total du calendrier. Ce compteur dépend des détails accessibles au jeton observateur. Ni noms de dépôts privés ni contenu des contributions ne sont publiés. Les contributions sont celles définies par GitHub ; elles ne mesurent pas la qualité du code ou le temps de travail.

Le script valide 365 dates et la cohérence des totaux avant de remplacer les fichiers. En cas d’erreur API, le workflow échoue et conserve les derniers graphiques. Si les données sont identiques, il évite les commits dus au seul passage du temps. Le push ne cible que `assets/activity.svg` et `assets/activity.json`, sans force push.

## Vérifications locales

```bash
python3 -m unittest discover -s tests -v
python3 scripts/compose_profile.py
GITHUB_TOKEN=… python3 scripts/activity.py --login SouphianeJ --output assets
```

Fournir le jeton via l’environnement ou un gestionnaire de secrets, sans le versionner. Les scripts utilisent uniquement la bibliothèque standard Python. Le script `scripts/preview_profile.py` permet de générer un aperçu HTML local ; GitHub conserve ses propres styles pour le texte Markdown.
