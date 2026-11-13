package com.wisertech.register.fixture.domain;

import java.util.List;

public final class Tally {
    public int countObligations(List<List<Integer>> rows) {
        int total = 0;
        for (List<Integer> row : rows) {
            for (int cell : row) {
                if (cell > 0) {
                    while (total < cell) {
                        total++;
                    }
                }
            }
        }
        return total;
    }
}
