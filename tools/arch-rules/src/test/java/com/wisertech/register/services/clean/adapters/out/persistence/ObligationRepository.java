package com.wisertech.register.services.clean.adapters.out.persistence;

import java.sql.Connection;
import java.sql.SQLException;
import javax.sql.DataSource;

/** Reads obligations from the service's own schema. */
public final class ObligationRepository {
    private final DataSource dataSource;

    public ObligationRepository(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /** Whether the database answers. */
    public boolean isReachable() throws SQLException {
        try (Connection connection = dataSource.getConnection()) {
            return connection.isValid(1);
        }
    }
}
