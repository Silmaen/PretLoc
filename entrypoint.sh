#!/usr/bin/env bash

set -e

# Fonction pour exécuter des commandes avec ou sans gosu
run_cmd() {
    if [ ! -z "${PUID}" ] && [ ! -z "${PGID}" ]; then
        gosu appuser "$@"
    else
        "$@"
    fi
}

# Créer les répertoires nécessaires s'ils n'existent pas
for dir in /app/data/migrations_data /app/nginx /app/staticfiles; do
    [[ -d $dir ]] || mkdir -p $dir
done
touch /app/migrations_data/__init__.py
for module in admin auth contenttypes sessions ui; do
    [[ -d /app/data/migrations_data/$module ]] || mkdir -p /app/data/migrations_data/$module
    touch /app/data/migrations_data/$module/__init__.py
done

# Créer le groupe et l'utilisateur avec les PUID/PGID fournis
if [ ! -z "${PUID}" ] && [ ! -z "${PGID}" ]; then
    echo "Configuring user with PUID: ${PUID} and PGID: ${PGID}"

    # Créer le groupe s'il n'existe pas
    if ! getent group appgroup > /dev/null 2>&1; then
        groupadd -g ${PGID} appgroup
    else
        # Si le groupe existe mais avec un GID différent
        groupmod -g ${PGID} appgroup
    fi

    # Créer l'utilisateur s'il n'existe pas
    if ! getent passwd appuser > /dev/null 2>&1; then
        useradd -u ${PUID} -g appgroup -m -s /bin/bash appuser
    else
        # Si l'utilisateur existe mais avec un UID différent
        usermod -u ${PUID} -g appgroup appuser
    fi

    # Attribuer les permissions aux dossiers nécessaires
    chown -R appuser:appgroup /app/data /app/staticfiles

else
    # Si PUID/PGID ne sont pas définis, exécuter normalement
    echo "No PUID/PGID provided, running as default user"
fi

# Attendre que la base de données soit disponible
echo "Wait PostgreSQL available..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "PostgreSQL now available !"


# Appliquer les migrations

echo "Generating migrations"
run_cmd python manage.py makemigrations
echo "Applying migrations"
run_cmd python manage.py migrate
echo "Compile messages"
chmod -R 777 /app/locale
run_cmd django-admin compilemessages

# Créer un superutilisateur si aucun n'existe
run_cmd echo "Check superuser exist..."
run_cmd python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', '${DJANGO_SUPERUSER_PASSWORD}');
    print('Superuser created');
else:
    print('Superuser already exist');
"

# Collecter les fichiers statiques
run_cmd python manage.py collectstatic --no-input --clear || echo "Collectstatic failed, continuing anyway"

# Démarrer l'application
if [ ! -z "${PUID}" ] && [ ! -z "${PGID}" ]; then
    exec gosu appuser gunicorn PretLoc.wsgi:application --bind 0.0.0.0:8000 --workers=3 --threads=2
else
    exec gunicorn PretLoc.wsgi:application --bind 0.0.0.0:8000 --workers=3 --threads=2
fi

