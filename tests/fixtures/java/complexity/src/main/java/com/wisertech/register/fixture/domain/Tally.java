package com.wisertech.register.fixture.domain;

public final class Tally {
    public String describeCriticality(int level, boolean isCritical) {
        if (isCritical && level > 9) {
            return "critical";
        }
        return switch (level) {
            case 0 -> "level 0";
            case 1 -> "level 1";
            case 2 -> "level 2";
            case 3 -> "level 3";
            case 4 -> "level 4";
            case 5 -> "level 5";
            case 6 -> "level 6";
            case 7 -> "level 7";
            case 8 -> "level 8";
            case 9 -> "level 9";
            default -> "unknown";
        };
    }
}
