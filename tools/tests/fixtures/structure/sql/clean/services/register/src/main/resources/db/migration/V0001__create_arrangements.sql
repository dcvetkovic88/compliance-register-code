-- The register's own table; reads the request context through the platform SQL interface.
-- A comment may name ictrisk.assessments without breaking the rule.
CREATE TABLE register.arrangements (
    arrangement_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL DEFAULT platform.current_tenant_id(),
    note text DEFAULT 'copied from ictrisk.assessments'
);
SELECT platform.publish('register.arrangement.created', '{}'::jsonb, gen_random_uuid());
SELECT pg_catalog.set_config('search_path', 'register', true);
-- SET search_path TO ictrisk; a comment is not read.
SET LOCAL search_path = register, pg_catalog;
CREATE INDEX IF NOT EXISTS arrangements_tenant ON register.arrangements (tenant_id);
SELECT a.arrangement_id, EXTRACT(YEAR FROM a.created_at), arrangements.note
FROM register.arrangements a
JOIN register.arrangements b ON a.arrangement_id = b.arrangement_id, register.arrangements
WHERE a.note IS DISTINCT FROM b.note;
INSERT INTO register.arrangements AS target (arrangement_id) VALUES (gen_random_uuid())
ON CONFLICT (arrangement_id) DO UPDATE SET note = EXCLUDED.note;
CREATE FUNCTION register.count_arrangements() RETURNS bigint LANGUAGE sql
AS 'SELECT count(*) FROM register.arrangements WHERE note <> ''copied from ictrisk.assessments''';
CREATE FUNCTION register.one() RETURNS int LANGUAGE sql SET search_path = register, pg_catalog AS $$ SELECT 1 $$;
CREATE FUNCTION register.two() RETURNS int LANGUAGE sql SET search_path TO 'register' AS 'SELECT 2';
CREATE SCHEMA IF NOT EXISTS register AUTHORIZATION cr_register;
GRANT USAGE ON SCHEMA register, pg_catalog TO cr_register;
ALTER DEFAULT PRIVILEGES IN SCHEMA register GRANT SELECT ON TABLES TO cr_register;
CREATE SEQUENCE register.arrangement_seq;
SELECT nextval('register.arrangement_seq'), currval('arrangement_seq'), 'pg_catalog.pg_class'::regclass;
SELECT setval('"register".arrangement_seq', 1), 'ictrisk.assessments is only a note';
