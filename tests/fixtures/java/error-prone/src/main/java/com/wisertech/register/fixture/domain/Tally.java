package com.wisertech.register.fixture.domain;

public final class Tally {
    public int countObligations(int first) {
        if (first < 0) {
            new IllegalArgumentException("negative count");
        }
        return first;
    }
}
