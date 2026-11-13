package com.wisertech.register.services.platform.domain;

public final class NoticeWindow {
    static final int MINIMUM_DAYS = 30;

    private NoticeWindow() {}
}

final class NoticeArithmetic {
    boolean allows(int days) {
        return days >= NoticeWindow.MINIMUM_DAYS;
    }
}
