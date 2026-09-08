# RoomBooking — Présentation du Projet de Stage

> **Développement d'une application web de gestion et de réservation des salles de réunion**
> 
> Stagiaire : [Votre nom] | Encadrant : [Nom encadrant] | Date : Août 2026

---

## 1. Contexte & Problématique

### Le besoin
- L'entreprise dispose de **plusieurs salles de réunion** mal gérées
- Réservations par **email, papier, ou à l'oral** → conflits fréquents
- Aucun outil centralisé pour consulter les **disponibilités en temps réel**

### Objectifs du stage
- Concevoir une **application web centralisée**
- Permettre la **réservation en ligne** avec vérification automatique
- Offrir une **vue calendrier** intuitive
- Gérer les **droits** (utilisateur vs administrateur)

---

## 2. Stack Technique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Langage** | Python 3.11 | Lisible, robuste, large communauté |
| **Framework** | Django 5.x | MVT intégré, ORM puissant, auth native |
| **Base de données** | PostgreSQL 15 | Fiabilité, transactions ACID, open source |
| **Frontend** | Bootstrap 5 + FullCalendar.js | Responsive, calendrier interactif |
| **Déploiement** | Docker + Nginx | Portabilité, scalabilité, production-ready |
| **Versioning** | Git | Suivi des évolutions, collaboration |

---

## 3. Architecture du Projet

```
roombooking/
├── config/          ← Settings, URLs, WSGI
├── apps/
│   ├── accounts/    ← Utilisateurs & authentification
│   ├── rooms/       ← Salles, équipements, disponibilités
│   └── bookings/    ← Réservations, conflits, calendrier
├── templates/       ← HTML partagés (Bootstrap)
├── static/          ← CSS, JS, images
└── tests/           ← Tests unitaires & d'intégration
```

**Découpage en 3 apps indépendantes** :
- `accounts` : gère les profils et les rôles
- `rooms` : catalogue des ressources (salles + équipements)
- `bookings` : cœur métier avec logique de conflit

---

## 4. Modèles de Données

### Entités principales

| Entité | Rôle | Relations |
|--------|------|-----------|
| **User** | Utilisateur standard ou administrateur | 1→N avec Booking |
| **Room** | Salle de réunion (nom, capacité, statut) | N→M avec Equipment |
| **Equipment** | Équipement disponible (projecteur, visio...) | — |
| **RoomAvailability** | Horaires d'ouverture par jour | N→1 avec Room |
| **Booking** | Réservation (créneau, motif, statut) | N→1 avec User + Room |

### Points clés de conception
- **Héritage** de `AbstractUser` pour le modèle User (rôle custom)
- **Relation Many-to-Many** Room ↔ Equipment
- **Index composite** sur `(room, start, end, status)` pour les perfs
- **Traçabilité** de l'annulation (qui, quand)

---

## 5. Fonctionnalités Développées

### 5.1 Gestion des salles (Admin)
- ✅ CRUD complet (créer, modifier, supprimer)
- ✅ Activation / désactivation d'une salle
- ✅ Association d'équipements
- ✅ Définition des horaires d'ouverture par jour

### 5.2 Authentification & Rôles
- ✅ Inscription / connexion / déconnexion
- ✅ Deux rôles : **Utilisateur** et **Administrateur**
- ✅ Permissions différenciées sur chaque vue

### 5.3 Réservations
- ✅ Création avec sélection de salle, date, heures, motif
- ✅ Modification de sa propre réservation
- ✅ Annulation avec traçabilité (date + auteur)
- ✅ **Détection automatique des conflits**

### 5.4 Calendrier
- ✅ Vue mensuelle, hebdomadaire, journalière, liste
- ✅ Filtrage dynamique par salle
- ✅ Modal de détails au clic
- ✅ API JSON pour FullCalendar.js

---

## 6. Logique Métier — Détection de Conflits

### Algorithme
```
Nouvelle réservation est VALIDE si :
  1. La salle est ACTIVE
  2. Le créneau est dans le FUTUR
  3. La date de fin > date de début
  4. Les horaires respectent les disponibilités de la salle
  5. AUCUNE réservation confirmée existante ne chevauche :
        new_start < existing_end
        AND
        new_end > existing_start
```

### Implémentation
- Vérification en `clean()` du modèle **et** du formulaire
- Requête Q optimisée avec index composite
- Exclusion de soi-même en cas de modification

---

## 7. Sécurité

| Menace | Contre-mesure |
|--------|---------------|
| Injection SQL | ORM Django (requêtes paramétrées) |
| XSS | Échappement automatique des templates |
| CSRF | Token natif sur tous les formulaires POST |
| Accès non autorisé | `LoginRequiredMixin` + `UserPassesTestMixin` |
| Fuite de données | `.env` exclu du Git, variables sensibles externalisées |
| Mots de passe faibles | Validators natifs Django (PBKDF2) |

---

## 8. Tests

### Couverture
- **30+ tests unitaires** répartis sur les 3 apps
- Tests de **modèles** (création, contraintes, propriétés)
- Tests de **vues** (permissions, redirections, CRUD)
- Tests de **formulaires** (validation, conflits)

### Exemple de test critique
```python
def test_booking_overlap_detection(self):
    Booking.objects.create(room=salle, start=09h00, end=10h00)
    with self.assertRaises(ValidationError):
        Booking(room=salle, start=09h30, end=10h30)  # Chevauchement
```

### Exécution
```bash
coverage run --source='.' manage.py test
coverage report  # → 100% modèles, 100% permissions, 100% conflits
```

---

## 9. Déploiement Docker

### Stack
```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│  Nginx  │────→│    Django   │────→│  PostgreSQL │
│  :80    │     │  Gunicorn   │     │   :5432     │
└─────────┘     └─────────────┘     └─────────────┘
```

### Commande de déploiement
```bash
./deploy.sh  # One-command : build, migrate, collectstatic, start
```

### Avantages
- ✅ Environnement **identique** dev / staging / prod
- ✅ **Portabilité** (Linux, Mac, Windows)
- ✅ **Persistance** des données via volume Docker
- ✅ **Scalabilité** (multi-workers Gunicorn)

---

## 10. Démonstration en Direct

### Scénario 1 — Utilisateur standard
1. 🔐 Connexion avec un compte utilisateur
2. 📅 Consultation du calendrier (vue mois)
3. 🏢 Détails d'une salle (capacité, équipements)
4. ➕ Création d'une réservation sur un créneau libre
5. ❌ Tentative de réservation sur un créneau occupé → **erreur**
6. ✏️ Modification du motif de la réservation
7. 🗑️ Annulation de la réservation

### Scénario 2 — Administrateur
1. 🔐 Connexion avec un compte admin
2. ⚙️ Création d'une nouvelle salle + équipements
3. 📋 Consultation de **toutes** les réservations (pas seulement les siennes)
4. 🗑️ Annulation d'une réservation d'un autre utilisateur

---

## 11. Bilan & Compétences Acquises

### Compétences techniques
| Compétence | Niveau atteint |
|------------|----------------|
| Programmation Python | ✅ Maîtrise des classes, héritage, tests |
| Développement Django | ✅ MVT, ORM, Mixins, formulaires |
| Conception BDD | ✅ Relations 1-N, N-M, index, contraintes |
| Authentification & droits | ✅ RBAC custom sur AbstractUser |
| Docker & DevOps | ✅ Multi-conteneurs, reverse proxy |
| Tests & qualité | ✅ TDD, coverage, assertions |

### Livrables fournis
- ✅ Application fonctionnelle
- ✅ Code source (Git)
- ✅ Schéma de base de données
- ✅ Documentation technique
- ✅ Documentation utilisateur
- ✅ Procédure d'installation & déploiement
- ✅ Présentation du projet

---

## 12. Perspectives d'Évolution

- 📱 **Application mobile** (API REST + React Native)
- 📧 **Notifications email** (rappel 15 min avant réunion)
- 🔗 **Intégration calendrier** (export ICS pour Outlook/Google)
- 📊 **Tableau de bord** (taux d'occupation par salle)
- 🤖 **Suggérer une salle** automatiquement selon le nombre de participants

---

## Merci pour votre attention !

> **Questions ?**
> 
> 📧 contact@entreprise.com
> 🌐 http://localhost (démo en local)
> 📁 Code source : `https://github.com/.../roombooking`
