package com.wisertech.register.fixture.domain;

import java.util.List;

/** Each method sits exactly at a size limit of conventions section 11, which the build allows. */
public final class CriticalityLimits {
    public int sumObligations(int first, int second, int third, int fourth) {
        int total = second + third + fourth;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        total += first;
        return total;
    }

    public int countPositiveCells(List<List<Integer>> rows) {
        int total = 0;
        for (List<Integer> row : rows) {
            for (int cell : row) {
                if (cell > 0) {
                    total++;
                }
            }
        }
        return total;
    }

    public String describeCriticality(int level, boolean isCritical) {
        if (isCritical) {
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
            default -> "unknown";
        };
    }
}
