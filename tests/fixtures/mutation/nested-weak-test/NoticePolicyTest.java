package com.wisertech.register.services.platform.domain;

import org.junit.jupiter.api.Test;

class NoticePolicyTest {
    @Test
    void runsTheNestedRuleWithoutCheckingTheResult() {
        new NoticePolicy.Rule(30).allows(10);
    }
}
