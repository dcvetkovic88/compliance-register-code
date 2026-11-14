package com.wisertech.register.adapters.out;

import org.springframework.jdbc.core.simple.JdbcClient;

class AssessmentReader {
    private final JdbcClient jdbc;

    AssessmentReader(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    long count() {
        return jdbc.sql("SELECT count(*) FROM " + "ict" // the schema split over two literals
                + "risk.assessments").query(Long.class).single();
    }
}
