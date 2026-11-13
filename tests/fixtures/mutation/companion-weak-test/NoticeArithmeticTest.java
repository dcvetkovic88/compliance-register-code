package com.wisertech.register.services.platform.domain;

import org.junit.jupiter.api.Test;

class NoticeArithmeticTest {
    @Test
    void runsTheCompanionClassWithoutCheckingTheResult() {
        new NoticeArithmetic().allows(10);
    }
}
