package com.wisertech.register.fixture.domain;

public final class Tally {
    public int countObligations(int first, int second, int third, int fourth) {
        int total = 0;
        if (first > 0) if (second > 0) if (third > 0) if (fourth > 0) total++;
        return total;
    }
}
