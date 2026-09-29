<div align="center">

# 📻 La 1ère Monitor

**Collecteur & Dashboard de la programmation musicale du réseau La 1ère**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=for-the-badge)](https://github.com/gunout)
[![Maintained](https://img.shields.io/badge/Maintained-yes-success?style=for-the-badge)](https://github.com/gunout/la1ere-monitor)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://github.com/gunout/la1ere-monitor/pulls)

---

*Collecte en continu · Enrichissement iTunes · Dashboard multi-radios · Analyse complète*

</div>

---

## 📖 Table des matières

- [Aperçu](#-aperçu)
- [Fonctionnalités](#-fonctionnalités)
- [Radios collectées](#-radios-collectées)
- [Architecture](#️-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Automatisation](#-automatisation)
- [Sources de données](#-sources-de-données)
- [Contribuer](#-contribuer)
- [Licence](#-licence)

---

## 🎯 Aperçu

**La 1ère Monitor** est un pipeline complet qui :

1. **Collecte** en temps réel les morceaux diffusés sur les 10 radios du réseau La 1ère (Outre-mer) via leurs flux Icecast
2. **Enrichit** automatiquement chaque morceau (artiste, album, année, pochette, extrait audio) via l'API publique iTunes
3. **Analyse** les données pour produire des CSV et un JSON multi-radios
4. **Affiche** le tout dans un dashboard HTML interactif avec onglets par radio

Idéal pour suivre la programmation musicale de chaque territoire d'Outre-mer, comparer les radios, ou découvrir la scène musicale locale.

---

## ✨ Fonctionnalités

### 🎧 Collecte & Enrichissement

- [x] Écoute simultanée des 10 flux Icecast du réseau La 1ère
- [x] Extraction des métadonnées `StreamTitle` (artiste + titre)
- [x] Détection anti-doublons (vérification en base avant insertion)
- [x] Stockage incrémental dans une base SQLite commune
- [x] Enrichissement iTunes : album, année, pochette 600×600, extrait audio 30s
- [x] Calcul de la durée de diffusion (start_ts / end_ts)

### 📊 Analyses

- [x] Volume global (diffusions, artistes, titres, heures)
- [x] Top artistes (temps d'antenne)
- [x] Top titres (nombre de diffusions)
- [x] Répartition horaire (24h)
- [x] Répartition journalière (évolution par date)
- [x] Top artiste par heure
- [x] Artistes récurrents (multi-jours)
- [x] Titres récurrents (multi-jours)
- [x] Artistes diversifiés
- [x] Répartition par année de sortie
- [x] Ratio Clean / Explicit
- [x] Top albums
- [x] Récap par radio

### 🎨 Dashboard

- [x] Design aux couleurs de France TV (bleu, vert, jaune)
- [x] Onglets dynamiques : un par radio + « Toutes »
- [x] Filtrage complet par radio (graphiques, tableaux, KPI)
- [x] Bandeau « On Air » avec pochette et compteur temps réel
- [x] Graphiques interactifs Plotly
- [x] Extrait audio iTunes au clic
- [x] Responsive (mobile / desktop)
- [x] Auto-refresh toutes les 2 minutes

---

## 📻 Radios collectées

| Radio | Territoire |
|-------|------------|
| **Outremer 1ère** | Réseau national |
| **Réunion 1ère** | La Réunion |
| **Martinique 1ère** | Martinique |
| **Guadeloupe 1ère** | Guadeloupe |
| **Guyane 1ère** | Guyane |
| **Mayotte 1ère** | Mayotte |
| **Nouvelle-Calédonie 1ère** | Nouvelle-Calédonie |
| **Wallis et Futuna 1ère** | Wallis-et-Futuna |
| **Saint-Pierre et Miquelon 1ère** | Saint-Pierre-et-Miquelon |
| **Polynésie 1ère** | Polynésie française |

---

## 🏗️ Architecture

| Fichier | Rôle |
|---------|------|
| `config.py` | Liste des 10 radios avec leurs URLs Icecast |
| `collecteur.py` | Écoute parallèle des flux + anti-doublons |
| `enrichir.py` | Enrichissement via l'API iTunes |
| `analyser.py` | Génération des CSV d'analyse |
| `export_json.py` | Génération du JSON pour le dashboard |
| `index.html` | Dashboard interactif multi-radios |
| `la1ere.db` | Base SQLite commune |
| `resultats/` | CSV générés |
| `data.json` | JSON pour le dashboard |

**Flux de données :**

1. Le collecteur ouvre 10 connexions Icecast en parallèle
2. Chaque flux envoie son `StreamTitle` toutes les 16 Ko
3. Le collecteur détecte les nouveaux morceaux et les insère dans `la1ere.db`
4. `enrichir.py` complète les métadonnées via iTunes
5. `analyser.py` produit les CSV
6. `export_json.py` produit `data.json`
7. `index.html` lit le JSON et affiche les graphiques

---

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- pip

### Cloner le dépôt

Ouvrez un terminal et tapez :

`git clone https://github.com/gunout/la1ere-monitor.git`

Puis :

`cd la1ere-monitor`

### Installer les dépendances

`pip install requests pandas`

---

## 🎮 Utilisation

### Étape 1 — Lancer le collecteur

`python3 collecteur.py`

Le collecteur se connecte aux 10 radios et enregistre les morceaux en temps réel.

**Pour le lancer en arrière-plan :**

`nohup python3 collecteur.py > /dev/null 2>&1 &`

### Étape 2 — Générer les analyses

`python3 analyser.py`

Produit les CSV dans le dossier `resultats/`.

### Étape 3 — Générer le JSON

`python3 export_json.py`

Produit `data.json`.

### Étape 4 — Lancer le dashboard

`python3 -m http.server 8006`

Puis ouvrez dans votre navigateur :

[http://localhost:8006/index.html](http://localhost:8006/index.html)

---

## ⏰ Automatisation

Pour régénérer les analyses et le JSON automatiquement toutes les minutes, éditez votre crontab avec :

`crontab -e`

Puis ajoutez la ligne suivante :

`* * * * * cd /chemin/vers/la1ere-monitor && /usr/bin/python3 analyser.py && /usr/bin/python3 export_json.py >> cron.log 2>&1`

---

## 🌐 Sources de données

| Source | Endpoint | Authentification |
|--------|----------|------------------|
| La 1ère (Icecast) | `https://{territoire}.ice.infomaniak.ch/{territoire}-128.mp3` | ❌ Aucune |
| iTunes Search | `https://itunes.apple.com/search` | ❌ Aucune |

---

## 🤝 Contribuer

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez une branche : `git checkout -b feature/ma-fonctionnalite`
3. Committez : `git commit -m "feat: ajoute ma fonctionnalité"`
4. Pushez : `git push origin feature/ma-fonctionnalite`
5. Ouvrez une Pull Request

### Convention de commit

- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `chore:` tâches diverses

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## ⚠️ Avertissement

- Les flux Icecast utilisés sont publics et destinés à l'écoute en direct.
- Ce projet est destiné à un **usage personnel et éducatif**.
- Les données musicales collectées restent la propriété de leurs ayants droit respectifs.
- L'auteur n'est pas affilié à France Télévisions ni au réseau La 1ère.

---

<div align="center">

**⭐ Si ce projet vous plaît, mettez-lui une étoile ! ⭐**

[🔝 Retour en haut](#-la-1ère-monitor)

</div>

---

<div align="center">

### 🇫🇷 Gunout · 2026

![Made in France](https://img.shields.io/badge/Made_in-France-002395?style=flat-square&labelColor=FFFFFF&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5MDAgNjAwIj48cmVjdCB3aWR0aD0iOTAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iIzAwMjM5NSIvPjxyZWN0IHdpZHRoPSI5MDAiIGhlaWdodD0iNDAwIiB5PSIxMDAiIGZpbGw9IiNmZmYiLz48cmVjdCB3aWR0aD0iOTAwIiBoZWlnaHQ9IjIwMCIgeT0iNDAwIiBmaWxsPSIjZWQyOTM5Ii8+PC9zdmc+)
![GitHub](https://img.shields.io/badge/GitHub-gunout-181717?style=flat-square&logo=github&logoColor=white)
![Year](https://img.shields.io/badge/2026-ED2939?style=flat-square&labelColor=FFFFFF)

<sub>© 2026 <strong>Gunout</strong> — Tous droits réservés.</sub>

</div>
