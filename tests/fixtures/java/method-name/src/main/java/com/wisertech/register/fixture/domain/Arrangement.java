package com.wisertech.register.fixture.domain;

public record Arrangement(String arrangementId) {
    public boolean Is_named() {
        return !arrangementId.isBlank();
    }
}
