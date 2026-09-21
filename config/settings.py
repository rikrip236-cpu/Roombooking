"""
Django settings for RoomBooking — Compatible MySQL (Laragon) / PostgreSQL / SQLite
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.rooms',
    'apps.bookings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.TimezoneDisplayMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================
# BASE DE DONNÉES — CHOIX PAR VARIABLE D'ENVIRONNEMENT
# ============================================================
# Définissez DB_ENGINE dans votre .env :
#   DB_ENGINE=mysql     → MySQL (Laragon, XAMPP, etc.)
#   DB_ENGINE=postgres  → PostgreSQL (par défaut)
#   DB_ENGINE=sqlite    → SQLite (test rapide, aucun serveur requis)
# ============================================================

DB_ENGINE = config('DB_ENGINE', default='postgres').lower()

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='roombooking'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                # SET time_zone='+00:00' force explicitement CHAQUE session
                # MySQL en UTC numérique dès la connexion. C'est nécessaire
                # en plus de TIME_ZONE='UTC' côté Django : par défaut, le
                # fuseau horaire MySQL est souvent réglé sur "SYSTEM" (celui
                # de l'OS Windows, ex. Europe/Paris). Or MySQL doit résoudre
                # ce nom via les tables système mysql.time_zone_name pour
                # certaines requêtes (ex. date_hierarchy de l'admin Django),
                # tables absentes par défaut sur une installation Laragon.
                # Résultat sans ce réglage : l'erreur persiste même avec
                # TIME_ZONE='UTC' côté Django, car MySQL, lui, reste sur
                # "SYSTEM". Un décalage numérique comme '+00:00' ne nécessite
                # AUCUNE table de nommage de fuseau : il fonctionne toujours,
                # sans dépendance d'installation supplémentaire.
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', time_zone='+00:00'",
            },
        }
    }
elif DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:  # postgres par défaut
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='roombooking'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
# TIME_ZONE reste en UTC pour la BASE DE DONNÉES : c'est volontaire.
# Avec USE_TZ=True, Django stocke toujours les dates en UTC dans la base et
# les convertit à l'affichage/saisie selon TIME_ZONE_DISPLAY (ci-dessous).
# Utiliser une TIME_ZONE non-UTC ici obligerait MySQL à faire des conversions
# de fuseau horaire (CONVERT_TZ) qui nécessitent les tables système
# mysql.time_zone*, absentes par défaut sur une installation Laragon/Windows.
# Résultat sans ces tables : "ValueError: Database returned an invalid
# datetime value. Are time zone definitions for your database installed?"
# (notamment sur la hiérarchie de dates de l'admin Django).
# → Garder TIME_ZONE='UTC' évite ce problème sans dépendre d'une installation
#   MySQL supplémentaire. Voir docs/TIMEZONE_MYSQL.md pour l'alternative
#   (installer les tables tz) si vous préférez stocker en Europe/Paris.
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Fuseau horaire utilisé uniquement pour l'affichage côté application
# (calendrier, listes, formulaires). Les dates restent stockées en UTC en
# base ; Django les convertit à la volée pour l'affichage/la saisie.
TIME_ZONE_DISPLAY = 'Europe/Paris'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

LOGIN_REDIRECT_URL = 'bookings:calendar'
LOGOUT_REDIRECT_URL = 'accounts:login'

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
