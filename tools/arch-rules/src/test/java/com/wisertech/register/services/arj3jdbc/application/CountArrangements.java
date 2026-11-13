package com.wisertech.register.services.arj3jdbc.application;

import java.sql.Connection;
import java.sql.SQLException;

public final class CountArrangements {
    public boolean countArrangements(Connection connection) throws SQLException {
        return connection.isValid(1);
    }
}
