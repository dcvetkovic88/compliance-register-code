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
