package com.wisertech.register.fixture.domain;

public record Fixture(int days) {
    public boolean isLongerThan(int otherDays) {
        return days > otherDays;
    }
}
