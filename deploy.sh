#!/bin/bash
set -e
echo "Deploiement RoomBooking"
if ! command -v docker &> /dev/null; then echo "Docker non installe"; exit 1; fi
if ! command -v docker-compose &> /dev/null; then echo "Docker Compose non installe"; exit 1; fi
if [ ! -f .env ]; then cp .env.production .env; echo ".env cree - modifiez SECRET_KEY!"; fi
docker-compose build
docker-compose up -d
sleep 5
docker-compose exec web python manage.py migrate --noinput
echo "RoomBooking deploye! http://localhost"
