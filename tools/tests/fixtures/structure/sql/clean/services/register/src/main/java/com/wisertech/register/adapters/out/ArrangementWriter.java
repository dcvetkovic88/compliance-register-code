package com.wisertech.register.adapters.out;

import org.springframework.jdbc.core.simple.JdbcClient;

/** Writes the register's own arrangements; a comment may name ictrisk.assessments, it is not read. */
class ArrangementWriter {
    private static final String CONSUMED_EVENT = "ictrisk.assessment.completed";
    private final JdbcClient jdbc;

    ArrangementWriter(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    // SELECT * FROM ictrisk.assessments in a comment is not read either.
    void insert(String name) {
        jdbc.sql("""
                INSERT INTO register.arrangements (arrangement_id, tenant_id, name)
                VALUES (gen_random_uuid(), platform.current_tenant_id(), :name)
                """).param("name", name).update();
        jdbc.sql("SELECT platform.publish('register.arrangement.created', '{}'::jsonb, gen_random_uuid())").query();
        jdbc.sql("SET LOCAL search_path = register, pg_catalog").update();
    }
}
