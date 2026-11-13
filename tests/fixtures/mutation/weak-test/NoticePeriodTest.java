package com.wisertech.register.services.platform.domain;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;

class NoticePeriodTest {
    @Test
    void runsWithoutCheckingTheResult() {
        NoticePeriod period = new NoticePeriod(30);

        period.isLongerThan(10);

        assertNotNull(period.extendBy(5));
    }
}
