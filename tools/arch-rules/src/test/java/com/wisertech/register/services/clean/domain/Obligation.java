package com.wisertech.register.services.clean.domain;

import java.math.BigDecimal;
import java.time.Instant;

public record Obligation(String obligationId, String regulationVersion, BigDecimal penaltyRate, Instant dueAt) {}
