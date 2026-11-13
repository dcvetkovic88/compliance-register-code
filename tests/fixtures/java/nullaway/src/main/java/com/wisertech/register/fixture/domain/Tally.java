package com.wisertech.register.fixture.domain;

public final class Tally {
    public String findObligationTitle(String obligationId) {
        return obligationId.isBlank() ? null : obligationId;
    }
}
