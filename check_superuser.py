"""
Utilitaire appelé par start.bat pour savoir si un compte administrateur existe deja.
Code de sortie 0 : un superutilisateur existe.
Code de sortie 1 : aucun superutilisateur, ou erreur (base non prete, etc.).
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    from apps.accounts.models import User
    sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)
except Exception:
    sys.exit(1)
