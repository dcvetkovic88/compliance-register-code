package com.wisertech.register.adapters.out;

import org.springframework.jdbc.core.simple.JdbcClient;

class AssessmentReader {
    private final JdbcClient jdbc;

    AssessmentReader(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    long count() {
        return jdbc.sql("SELECT count(*) FROM ictrisk.assessments").query(Long.class).single();
    }
}
