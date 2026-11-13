package com.wisertech.register.services.platform.adapters.out;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;

class NoticeStoreTest {
    @Test
    void runsWithoutCheckingTheResult() {
        NoticeStore period = new NoticeStore(30);

        period.isLongerThan(10);

        assertNotNull(period.extendBy(5));
    }
}
