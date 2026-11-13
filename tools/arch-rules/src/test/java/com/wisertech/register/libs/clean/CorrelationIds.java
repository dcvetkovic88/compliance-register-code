package com.wisertech.register.libs.clean;

import java.util.UUID;

public final class CorrelationIds {
    private CorrelationIds() {}

    public static String newCorrelationId() {
        return UUID.randomUUID().toString();
    }
}
