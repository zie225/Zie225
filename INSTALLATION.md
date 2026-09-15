# Installation — profil GitHub de Mamadou

## Pourquoi tu avais une erreur 404

Ton `README.md` demandait :

- `profile/stats.svg`
- `profile/top-langs.svg`
- `profile/streak.svg`

mais ces fichiers n'existaient pas dans la branche `master` de ton dépôt. GitHub affichait donc uniquement le texte alternatif des images et la page du SVG retournait `404 - page not found`.

## Installation correcte

Tu dois envoyer **tout le contenu du ZIP**, pas seulement `README.md`.

La racine du dépôt `Zie225/Zie225` doit contenir exactement :

```text
README.md
INSTALLATION.md
profile/
├── stats.svg
├── top-langs.svg
└── streak.svg
.github/
└── workflows/
    └── update-profile-cards.yml
```

## Première exécution

1. Commit/push tous ces fichiers sur la branche par défaut (`master` chez toi d'après la capture).
2. Vérifie que `profile/stats.svg` existe bien dans GitHub.
3. Va dans `Actions`.
4. Ouvre `Update Profile Cards`.
5. Clique sur `Run workflow`.
6. Le workflow remplacera les trois SVG placeholders par tes vraies statistiques.

## Autorisation nécessaire si le push du workflow échoue

Dans GitHub :

`Settings → Actions → General → Workflow permissions`

Choisis l'option qui autorise les GitHub Actions à écrire dans le dépôt, puis sauvegarde.

## Pourquoi cette version est plus robuste

Les cartes sont générées par GitHub Actions et stockées directement dans ton dépôt. Le README n'appelle donc pas un service Vercel ou Heroku à chaque affichage.

- Stats + Top Languages : `stats-organization/github-readme-stats-action@v2`
- Streak : `zients/github-readme-streak-stats@v2`

Le workflow utilise automatiquement `secrets.GITHUB_TOKEN`; aucun token personnel n'est écrit dans le README.
