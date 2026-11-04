-- Runs once, as the superuser, when the data directory is first created. See init.sh.
\set ON_ERROR_STOP on

CREATE ROLE samvid_owner LOGIN PASSWORD :'owner_password';
CREATE ROLE samvid_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE openfga LOGIN PASSWORD :'openfga_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;

CREATE DATABASE samvid OWNER samvid_owner;
CREATE DATABASE openfga OWNER openfga;

REVOKE ALL ON DATABASE samvid FROM PUBLIC;
REVOKE ALL ON DATABASE openfga FROM PUBLIC;
GRANT CONNECT ON DATABASE samvid TO samvid_app;

\connect samvid

-- pgvector isn't a trusted extension, so only a superuser can create it.
CREATE EXTENSION IF NOT EXISTS vector;

ALTER SCHEMA public OWNER TO samvid_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO samvid_app;
