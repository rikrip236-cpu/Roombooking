# RoomBooking — Application de Réservation de Salles

## 📋 Table des matières
1. [Architecture](#architecture)
2. [Stack technique](#stack-technique)
3. [Modèles de données](#modèles-de-données)
4. [Installation](#installation)
5. [Déploiement Docker](#déploiement-docker)
6. [Tests](#tests)
7. [API JSON](#api-json)
8. [Sécurité](#sécurité)

---

## Architecture

```
roombooking/
├── config/              # Configuration Django (settings, urls, wsgi)
├── apps/
│   ├── accounts/        # Gestion des utilisateurs et authentification
│   ├── rooms/           # Gestion des salles et équipements
│   └── bookings/        # Gestion des réservations et calendrier
├── templates/           # Templates HTML partagés
├── static/              # CSS, JS, images
├── tests/               # Tests unitaires et d'intégration
├── requirements.txt
├── docker-compose.yml
└── .env
```

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.11+, Django 5.x |
| Base de données | PostgreSQL 15+ |
| Frontend | HTML5, Bootstrap 5, Bootstrap Icons |
| Authentification | Django auth (session-based) |
| Déploiement | Docker + Docker Compose (optionnel) |
| Tests | Django TestCase + Coverage |

---

## Modèles de données

### User (`accounts`)
Étend `AbstractUser`. Champs additionnels :
- `role` : `user` ou `admin`
- `phone`, `department`

### Room (`rooms`)
- `name` (unique), `capacity`, `description`, `is_active`
- Relation M2M avec `Equipment`

### Equipment (`rooms`)
- `name` (unique), `description`, `icon`

### RoomAvailability (`rooms`)
- Horaires d'ouverture par salle et par jour de semaine
- `day_of_week` (0-6), `open_time`, `close_time`, `is_closed`

### Booking (`bookings`)
- `user` (FK), `room` (FK), `title`, `start_datetime`, `end_datetime`
- `status` : `confirmed` | `cancelled`
- `cancelled_at`, `cancelled_by` (traçabilité)
- Index composite : `(room, start_datetime, end_datetime, status)`

---

## Installation

### 🚀 Démarrage rapide sous Windows (Laragon)

Un script `start.bat` est fourni à la racine du projet. Il automatise tout :
création de l'environnement virtuel, installation des dépendances, copie du
`.env`, création de la base MySQL, migrations, chargement des données de
démo, création d'un compte admin si besoin, et lancement du serveur.

1. Démarrer Laragon (bouton **Start All**, MySQL doit tourner sur le port 3306).
2. Double-cliquer sur **`start.bat`** à la racine du projet
   (ou depuis une invite de commandes : `start.bat`).
3. Le navigateur s'ouvre automatiquement sur http://127.0.0.1:8000/
4. Pour arrêter le serveur : `Ctrl+C` dans la fenêtre, ou double-cliquer sur `stop.bat`.

Relancer `start.bat` les fois suivantes ne recrée rien d'inutile : il détecte
l'environnement virtuel, la base et les données déjà en place et démarre
directement le serveur.

> Si Python n'est pas reconnu, installez-le depuis https://python.org en
> cochant **"Add Python to PATH"**, puis relancez `start.bat`.

### Prérequis (installation manuelle)
- Python 3.11+
- PostgreSQL 15+ (ou MySQL via Laragon, voir `.env.laragon`)
- Git

### 1. Cloner le projet
```bash
git clone <repo-url>
cd roombooking
```

### 2. Environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

### 3. Dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
Créer un fichier `.env` à la racine :
```env
SECRET_KEY=votre-cle-secrete-64-caracteres-aleatoires
DEBUG=True
DB_NAME=roombooking
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 5. Base de données
```bash
# Créer la base PostgreSQL
createdb roombooking

# Migrations
python manage.py migrate

# Super-utilisateur
python manage.py createsuperuser

# Données de démonstration (optionnel)
python manage.py loaddata fixtures/demo.json
```

### 6. Lancer le serveur
```bash
python manage.py runserver
# Accès : http://127.0.0.1:8000/
# Admin  : http://127.0.0.1:8000/admin/
```

---

## Déploiement Docker

### Fichier `docker-compose.yml`
```yaml
version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: roombooking
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  pgdata:
```

### Fichier `Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### Commandes
```bash
docker-compose up --build
```

---

## Tests

### Lancer les tests
```bash
# Tous les tests
python manage.py test

# Avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html  # Rapport HTML dans htmlcov/
```

### Structure des tests
```
apps/
├── accounts/tests.py
├── rooms/tests.py
└── bookings/tests.py
```

---

## API JSON

Endpoint pour le calendrier interactif (FullCalendar.js compatible) :

```
GET /bookings/api/events/?start=2024-01-01&end=2024-01-31&room=1
```

Réponse :
```json
[
  {
    "id": 1,
    "title": "Réunion projet — Salle A",
    "start": "2024-01-15T09:00:00+01:00",
    "end": "2024-01-15T10:30:00+01:00",
    "extendedProps": {
      "room": "Salle A",
      "user": "Jean Dupont",
      "capacity": 10
    },
    "backgroundColor": "#3b82f6"
  }
]
```

---

## Sécurité

| Mesure | Implémentation |
|--------|---------------|
| CSRF | Protection native Django sur tous les formulaires POST |
| Authentification | Session-based, middleware intégré |
| Autorisation | `LoginRequiredMixin`, `UserPassesTestMixin` |
| Injection SQL | ORM Django (requêtes paramétrées) |
| XSS | Échappement automatique des templates |
| Mots de passe | PBKDF2 (algo natif Django) |
| Variables sensibles | Fichier `.env` exclu du Git |
| Comptes | Modèle `User` personnalisé enregistré dans le Django Admin |

---

## Auteur
Développé dans le cadre du stage de découverte Django/Python.
