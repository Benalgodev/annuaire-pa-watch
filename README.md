# annuaire-pa-watch

[![Veille](https://github.com/Benalgodev/annuaire-pa-watch/actions/workflows/watch.yml/badge.svg)](https://github.com/Benalgodev/annuaire-pa-watch/actions)

Chaque lundi, une GitHub Action récupère la **liste officielle des plateformes agréées** publiée par la DGFiP, la convertit en CSV et inscrit dans [CHANGELOG.md](CHANGELOG.md) ce qui a changé : nouvelles plateformes, retraits, changements de statut.

## Pourquoi

Une entreprise doit choisir sa plateforme agréée et un éditeur ERP doit savoir avec quelles plateformes il interopère. La liste évolue au fil des immatriculations ; personne n'en garde l'historique. Ce dépôt en est le journal.

## Données

- `data/plateformes.csv` : dernière version de la liste, normalisée
- `data/meta.json` : source, date, empreinte SHA-256 du fichier officiel
- `CHANGELOG.md` : historique des changements

Source : impots.gouv.fr. Les données restent celles de l'administration ; ce dépôt n'en modifie pas le contenu.
