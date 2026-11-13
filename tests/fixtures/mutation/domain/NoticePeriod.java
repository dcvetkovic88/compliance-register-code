package com.wisertech.register.services.platform.domain;

public record NoticePeriod(int days) {
    public boolean isLongerThan(int otherDays) {
        return days > otherDays;
    }

    public NoticePeriod extendBy(int extraDays) {
        return new NoticePeriod(days + extraDays);
    }
}
