#!/bin/sh
# The Postgres image runs *.sql files without variables, so this passes the role passwords in.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v owner_password="$SAMVID_OWNER_PASSWORD" \
    -v app_password="$SAMVID_APP_PASSWORD" \
    -v openfga_password="$OPENFGA_DB_PASSWORD" \
    -f /docker-entrypoint-initdb.d/sql/init.sql
