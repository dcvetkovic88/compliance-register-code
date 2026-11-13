package com.wisertech.register.services.platform.domain;

public final class NoticePolicy {
    private NoticePolicy() {}

    public record Rule(int minimumDays) {
        public boolean allows(int days) {
            return days >= minimumDays;
        }
    }
}
