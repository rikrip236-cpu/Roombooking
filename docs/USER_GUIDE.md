# RoomBooking — Guide Utilisateur

## 🔐 Connexion & Inscription

### Créer un compte
1. Cliquez sur **S'inscrire** en haut à droite.
2. Remplissez le formulaire (nom, prénom, email, nom d'utilisateur, mot de passe).
3. Validez. Vous pouvez ensuite vous connecter.

### Se connecter
1. Cliquez sur **Connexion**.
2. Saisissez votre nom d'utilisateur et mot de passe.
3. Vous êtes redirigé vers le calendrier des réservations.

---

## 📅 Consulter le calendrier

La page d'accueil affiche un **calendrier mensuel** :
- Les réservations apparaissent sous forme de pastilles colorées.
- Utilisez les flèches **< >** pour changer de mois.
- Cliquez sur **Aujourd'hui** pour revenir au mois en cours.
- Filtrez par salle avec le menu déroulant en haut à droite.
- Cliquez sur une réservation pour voir ses détails.

---

## 🏢 Voir les salles

Dans le menu **Salles** :
- Liste de toutes les salles actives avec capacité et équipements.
- Cliquez sur **Détails** pour voir la description complète.

---

## ➕ Créer une réservation

1. Cliquez sur **Nouvelle réservation** (bouton vert).
2. Sélectionnez une **salle**.
3. Indiquez le **motif** de la réunion.
4. Choisissez la **date**, l'**heure de début** et l'**heure de fin**.
5. Validez.

> ⚠️ L'application vérifie automatiquement :
> - Que la salle n'est pas déjà réservée sur ce créneau.
> - Que la salle est ouverte à ces horaires.
> - Que vous ne réservez pas dans le passé.

---

## ✏️ Modifier une réservation

1. Allez dans **Mes réservations**.
2. Cliquez sur l'icône **crayon** (🖉) à côté de la réservation.
3. Modifiez les champs souhaités.
4. Validez.

> Vous ne pouvez modifier que **vos propres réservations**.

---

## ❌ Annuler une réservation

1. Dans **Mes réservations**, cliquez sur l'icône **croix** (✕).
2. Confirmez l'annulation.
3. La réservation passe au statut **Annulée** et disparaît du calendrier.

> L'annulation est **traçée** : date et auteur de l'annulation sont enregistrés.

---

## 🔍 Filtrer mes réservations

Dans la liste **Mes réservations**, utilisez les filtres :
- **Salle** : n'afficher qu'une salle spécifique.
- **Du / Au** : plage de dates.
- **Statut** : Confirmées ou Annulées.
- Cliquez sur **Filtrer** pour appliquer, ou **Réinitialiser** pour tout afficher.

---

## 👤 Profil utilisateur

Votre nom et rôle apparaissent dans la barre de navigation :
- **Utilisateur** : peut réserver, modifier et annuler ses propres réservations.
- **Administrateur** : peut en plus créer/modifier/supprimer des salles, gérer les équipements, et annuler n'importe quelle réservation.

---

## 📞 Support

En cas de problème, contactez l'administrateur via l'interface d'administration Django (`/admin/`) ou par email.
