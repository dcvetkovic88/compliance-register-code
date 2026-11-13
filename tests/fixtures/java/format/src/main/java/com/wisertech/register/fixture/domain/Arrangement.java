package com.wisertech.register.fixture.domain;

public record Arrangement(String arrangementId) {
    public boolean isNamed() { return !arrangementId.isBlank(); }
}
