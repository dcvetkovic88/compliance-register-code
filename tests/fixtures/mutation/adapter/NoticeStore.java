package com.wisertech.register.services.platform.adapters.out;

/** Keeps the notice period of an arrangement. */
public record NoticeStore(int days) {
    public boolean isLongerThan(int otherDays) {
        return days > otherDays;
    }

    public NoticeStore extendBy(int extraDays) {
        return new NoticeStore(days + extraDays);
    }
}
