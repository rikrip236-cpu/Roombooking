# Fuseau horaire & MySQL — pourquoi l'erreur "Are time zone definitions installed?"

## Le problème

Sur l'admin Django (`/admin/bookings/booking/`), la page plantait avec :

```
ValueError: Database returned an invalid datetime value.
Are time zone definitions for your database installed?
```

**Cause** : Django était configuré avec `TIME_ZONE = 'Europe/Paris'` et
`USE_TZ = True`. La hiérarchie de dates de l'admin (`date_hierarchy` sur
`BookingAdmin`) demande à MySQL de convertir les dates UTC stockées en base
vers l'heure de Paris directement en SQL (fonction `CONVERT_TZ`). Cette
fonction a besoin des tables système `mysql.time_zone*`, qui **ne sont pas
installées par défaut** sur une installation MySQL Windows/Laragon.

## La correction appliquée (par défaut dans ce projet)

`config/settings.py` utilise maintenant :

```python
TIME_ZONE = 'UTC'
USE_TZ = True
TIME_ZONE_DISPLAY = 'Europe/Paris'
```

- Les dates continuent d'être stockées en **UTC** en base (c'est déjà ce qui
  se passait avant, car avec `USE_TZ=True` la conversion vers UTC se fait
  côté Python à l'écriture, pas en SQL — **aucune donnée existante n'est
  affectée**).
- Comme `TIME_ZONE` est maintenant UTC, MySQL n'a plus besoin de convertir
  quoi que ce soit (UTC → UTC = identité), donc `CONVERT_TZ()` n'est plus
  sollicité et l'erreur disparaît.
- Un middleware (`apps/accounts/middleware.py`) active `TIME_ZONE_DISPLAY`
  ('Europe/Paris') à chaque requête, pour que les dates affichées dans
  l'application (calendrier, listes, formulaires, admin) restent bien en
  heure de Paris, comme avant.

**Aucune action nécessaire** : cette correction ne demande aucune migration
ni modification de la base de données.

## Alternative : installer les tables tz dans MySQL

Si vous préférez que `TIME_ZONE` reste directement `'Europe/Paris'` dans
`settings.py` (par exemple pour utiliser `CONVERT_TZ()` dans des requêtes
SQL personnalisées), vous pouvez installer les tables de fuseaux horaires
dans MySQL :

1. Sous Laragon, ouvrez un terminal (Menu → Terminal), puis :
   ```
   cd C:\laragon\bin\mysql\mysql-x.x.x\bin
   mysql_tzinfo_to_sql C:\laragon\usr\share\zoneinfo | mysql -u root mysql
   ```
   (Laragon n'embarque pas toujours `zoneinfo` sur Windows nativement — si le
   dossier n'existe pas, la méthode la plus simple sous Windows est de
   télécharger un jeu de tables tz déjà généré, par exemple depuis le paquet
   `mysql-timezone-tables` disponible sur le site officiel MySQL, puis de
   l'importer avec `mysql -u root mysql < timezone_posix.sql`.)

2. Redémarrez MySQL depuis Laragon.

3. Remettez `TIME_ZONE = 'Europe/Paris'` dans `config/settings.py` et retirez
   (ou laissez, c'est sans effet) le middleware `TimezoneDisplayMiddleware`.

Dans la grande majorité des cas, la solution par défaut (UTC + middleware
d'affichage) est plus simple à maintenir et évite toute dépendance à une
installation MySQL supplémentaire — c'est celle recommandée pour ce projet.
