package com.wisertech.register.services.arj9interface.domain;

public final class DefaultRiskScoring implements RiskScoring {
    @Override
    public int scoreRisk(String riskId) {
        return riskId.length();
    }
}
