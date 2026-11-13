package com.wisertech.register.fixture.domain;

public record Arrangement(String arrangementId) {
    // TODO check the notification period
    public boolean isNamed() {
        return !arrangementId.isBlank();
    }
}
