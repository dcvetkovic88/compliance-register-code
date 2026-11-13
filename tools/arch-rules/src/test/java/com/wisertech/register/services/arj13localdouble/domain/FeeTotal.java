package com.wisertech.register.services.arj13localdouble.domain;

import java.math.BigDecimal;

public final class FeeTotal {
    public BigDecimal total() {
        return BigDecimal.valueOf(0.1 + 0.2);
    }
}
