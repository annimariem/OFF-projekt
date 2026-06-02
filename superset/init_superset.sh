#!/bin/bash
set -e

superset db upgrade

superset fab create-admin \
  --username "$SUPERSET_ADMIN_USERNAME" \
  --firstname "$SUPERSET_ADMIN_FIRSTNAME" \
  --lastname "$SUPERSET_ADMIN_LASTNAME" \
  --email "$SUPERSET_ADMIN_EMAIL" \
  --password "$SUPERSET_ADMIN_PASSWORD" \
|| true

superset init

# Dashboardi ZIP-is parooli asendamine
echo "Fixing database password in dashboard export..."
mkdir -p /tmp/dash_fix
unzip -o /tmp/dashboards/dashboard.zip -d /tmp/dash_fix

# Moodustame õige URI
FULL_URI="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@analytics-db:5432/${POSTGRES_DB}"

# OTSINGU PARANDUS: Leiame YAML failid üles kõikidest alamkaustadest, kus on /databases/
echo "Searching for database YAML files..."
find /tmp/dash_fix -type f -path "*/databases/*.yaml" -exec sed -i "s|sqlalchemy_uri:.*|sqlalchemy_uri: ${FULL_URI}|" {} +

# Pakime uuesti kokku (läheme kausta sisse, et struktuur jääks samaks)
cd /tmp/dash_fix && zip -r /tmp/dashboard_fixed.zip .

# Importimine parandatud failiga
superset import-dashboards \
  --path /tmp/dashboard_fixed.zip \
  --username "$SUPERSET_ADMIN_USERNAME"

echo "Superset initialized successfully!"