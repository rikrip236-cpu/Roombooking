# RoomBooking — Schémas Mermaid

## 1. Diagramme Entité-Relation (Base de données)

```mermaid
erDiagram
    USER ||--o{ BOOKING : "crée"
    USER ||--o{ BOOKING : "annule"
    ROOM ||--o{ BOOKING : "est réservée dans"
    ROOM ||--o{ ROOM_AVAILABILITY : "a des horaires"
    ROOM }o--o{ EQUIPMENT : "possède"

    USER {
        bigint id PK
        string username UK
        string email UK
        string first_name
        string last_name
        string password
        string role "user|admin"
        string phone
        string department
        boolean is_active
        datetime date_joined
        datetime last_login
    }

    ROOM {
        bigint id PK
        string name UK
        int capacity
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    EQUIPMENT {
        bigint id PK
        string name UK
        text description
        string icon
    }

    ROOM_AVAILABILITY {
        bigint id PK
        int day_of_week "0-6"
        time open_time
        time close_time
        boolean is_closed
    }

    BOOKING {
        bigint id PK
        string title
        datetime start_datetime
        datetime end_datetime
        string status "confirmed|cancelled"
        datetime created_at
        datetime updated_at
        datetime cancelled_at
    }
```

---

## 2. Diagramme d'Architecture

```mermaid
graph TB
    subgraph "Client"
        Browser["🌐 Navigateur"]
    end

    subgraph "Serveur — Docker"
        Nginx["🔷 Nginx<br/>Port 80"]

        subgraph "App Container"
            Gunicorn["🐍 Gunicorn<br/>4 Workers"]
            Django["⚡ Django 5.x<br/> MVT + ORM"]
            Static["📁 Whitenoise<br/>Static Files"]
        end

        subgraph "DB Container"
            Postgres["🐘 PostgreSQL 15<br/>roombooking"]
        end
    end

    Browser -->|HTTP| Nginx
    Nginx -->|Proxy Pass| Gunicorn
    Nginx -->|/static/| Static
    Gunicorn --> Django
    Django -->|SQL| Postgres
```

---

## 3. Diagramme de Séquence — Création d'une Réservation

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant B as Navigateur
    participant D as Django
    participant F as BookingForm
    participant M as Modèle Booking
    participant DB as PostgreSQL

    U->>B: Sélectionne salle, date, heures
    U->>B: Soumet le formulaire
    B->>D: POST /bookings/create/
    D->>F: BookingForm(data, user)
    F->>F: clean() — validation

    alt Créneau invalide
        F->>F: end <= start ?
        F-->>D: ValidationError
        D-->>B: Formulaire avec erreurs
        B-->>U: Affiche erreur
    else Salle inactive
        F->>F: room.is_active == False ?
        F-->>D: ValidationError
        D-->>B: Formulaire avec erreurs
        B-->>U: Affiche erreur
    else Chevauchement détecté
        F->>DB: SELECT * FROM bookings WHERE room=X AND status='confirmed' AND overlap
        DB-->>F: 1 réservation trouvée
        F-->>D: ValidationError
        D-->>B: Formulaire avec erreurs
        B-->>U: "Salle déjà réservée"
    else Créneau valide
        F->>DB: SELECT ... overlap
        DB-->>F: 0 résultat
        F->>M: save()
        M->>DB: INSERT INTO bookings
        DB-->>M: OK
        M-->>F: Instance créée
        F-->>D: Instance valide
        D-->>B: Redirect 302
        B-->>U: "Réservation créée !"
    end
```

---

## 4. Diagramme de Cas d'Utilisation

```mermaid
graph LR
    subgraph "Acteurs"
        User["👤 Utilisateur"]
        Admin["🛡️ Administrateur"]
    end

    subgraph "Fonctionnalités"
        Auth["🔐 S'authentifier"]
        ViewRooms["🏢 Voir les salles"]
        Book["📅 Réserver une salle"]
        EditBook["✏️ Modifier sa réservation"]
        CancelBook["❌ Annuler sa réservation"]
        ViewCalendar["📆 Consulter le calendrier"]

        ManageRooms["⚙️ Gérer les salles"]
        ManageEquip["🔧 Gérer les équipements"]
        ViewAllBooks["📋 Voir toutes les réservations"]
        CancelAnyBook["🗑️ Annuler n'importe quelle réservation"]
    end

    User --> Auth
    User --> ViewRooms
    User --> Book
    User --> EditBook
    User --> CancelBook
    User --> ViewCalendar

    Admin --> Auth
    Admin --> ViewRooms
    Admin --> Book
    Admin --> EditBook
    Admin --> CancelBook
    Admin --> ViewCalendar
    Admin --> ManageRooms
    Admin --> ManageEquip
    Admin --> ViewAllBooks
    Admin --> CancelAnyBook
```

---

## 5. Diagramme de Flux de Données — API Calendrier

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant FC as FullCalendar.js
    participant API as /bookings/api/events/
    participant ORM as Django ORM
    participant DB as PostgreSQL

    U->>FC: Change de mois / filtre salle
    FC->>API: GET ?start=2026-08-01&end=2026-08-31&room=2
    API->>ORM: Booking.objects.filter(...)
    ORM->>DB: SELECT avec index composite
    DB-->>ORM: Résultats optimisés
    ORM-->>API: QuerySet
    API->>API: Sérialisation JSON
    API-->>FC: [{id, title, start, end, extendedProps, color}]
    FC->>FC: Rendu des événements
    FC-->>U: Calendrier mis à jour
```

---

## 6. Modèle Physique — Schéma SQL (PostgreSQL)

```sql
-- Table accounts_user (hérite de auth_user)
CREATE TABLE accounts_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    role VARCHAR(10) NOT NULL DEFAULT 'user',
    phone VARCHAR(20),
    department VARCHAR(100)
);

-- Table rooms_room
CREATE TABLE rooms_room (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Table rooms_equipment
CREATE TABLE rooms_equipment (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50)
);

-- Table de liaison Many-to-Many
CREATE TABLE rooms_room_equipment (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms_room(id) ON DELETE CASCADE,
    equipment_id BIGINT NOT NULL REFERENCES rooms_equipment(id) ON DELETE CASCADE,
    UNIQUE(room_id, equipment_id)
);

-- Table rooms_roomavailability
CREATE TABLE rooms_roomavailability (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL REFERENCES rooms_room(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    open_time TIME NOT NULL DEFAULT '08:00:00',
    close_time TIME NOT NULL DEFAULT '18:00:00',
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(room_id, day_of_week)
);

-- Table bookings_booking
CREATE TABLE bookings_booking (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    room_id BIGINT NOT NULL REFERENCES rooms_room(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by_id BIGINT REFERENCES accounts_user(id) ON DELETE SET NULL,
    CONSTRAINT check_end_after_start CHECK (end_datetime > start_datetime)
);

-- Index composite pour les performances
CREATE INDEX idx_booking_overlap ON bookings_booking 
    (room_id, start_datetime, end_datetime, status);
```
