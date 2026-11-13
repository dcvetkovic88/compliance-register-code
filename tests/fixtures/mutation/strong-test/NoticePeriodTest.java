package com.wisertech.register.services.platform.domain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class NoticePeriodTest {
    @Test
    void isLongerThanAShorterPeriodOnly() {
        NoticePeriod period = new NoticePeriod(30);

        assertTrue(period.isLongerThan(29));
        assertFalse(period.isLongerThan(30));
    }

    @Test
    void extendsByTheExtraDays() {
        assertEquals(new NoticePeriod(35), new NoticePeriod(30).extendBy(5));
    }
}
