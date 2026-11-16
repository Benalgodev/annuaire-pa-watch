# annuaire-pa-watch

[![Veille](https://github.com/Benalgodev/annuaire-pa-watch/actions/workflows/watch.yml/badge.svg)](https://github.com/Benalgodev/annuaire-pa-watch/actions)

Chaque lundi, une GitHub Action récupère la **liste officielle des plateformes agréées** publiée par la DGFiP, la convertit en CSV et inscrit dans [CHANGELOG.md](CHANGELOG.md) ce qui a changé : nouvelles plateformes, retraits, changements de statut.

## Pourquoi

Une entreprise doit choisir sa plateforme agréée et un éditeur ERP doit savoir avec quelles plateformes il interopère. La liste évolue au fil des immatriculations ; personne n'en garde l'historique. Ce dépôt en est le journal.

## Comment ça marche

Le dépôt applique le principe du *git scraping* : chaque passage du robot enregistre l'état de la liste dans un commit signé `github-actions[bot]`. L'historique Git devient l'historique de la liste. `git log -p data/plateformes.csv` montre qui est entré, sorti ou a changé de statut, et à quelle date, sans base de données.

```
impots.gouv.fr ──▶ watch/fetch.py ──▶ data/*.csv + CHANGELOG.md ──▶ commit du robot
   (lundi 6h17)     détection du fichier, normalisation, diff
```

Les commits du robot sont des données. Le code est versionné à part, dans des commits signés par l'auteur.

## Données

- `data/plateformes.csv` : dernière version de la liste, normalisée
- `data/meta.json` : source, date, empreinte SHA-256 du fichier officiel
- `CHANGELOG.md` : historique des changements

Source : impots.gouv.fr. Les données restent celles de l'administration ; ce dépôt n'en modifie pas le contenu.
