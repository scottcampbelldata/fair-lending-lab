-- Run as the postgres superuser on the VPS once, before deploying the app.
-- Replace REPLACE_ME with a strong password and save it to /home/scott/fair-lending-lab/platform/.env

CREATE ROLE flab_app WITH LOGIN PASSWORD 'REPLACE_ME' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT;
CREATE DATABASE fair_lending_lab OWNER flab_app ENCODING 'UTF8' TEMPLATE template0;
\c fair_lending_lab postgres
CREATE SCHEMA IF NOT EXISTS flab AUTHORIZATION flab_app;
GRANT ALL PRIVILEGES ON SCHEMA flab TO flab_app;
GRANT CONNECT ON DATABASE fair_lending_lab TO flab_app;

-- After this, run as the application user:
--   psql "postgresql://flab_app:REPLACE_ME@localhost:5432/fair_lending_lab" -f flab/db/schema.sql
