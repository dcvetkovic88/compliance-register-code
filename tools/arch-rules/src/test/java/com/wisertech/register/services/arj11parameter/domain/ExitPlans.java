package com.wisertech.register.services.arj11parameter.domain;

import java.util.Optional;

public final class ExitPlans {
    public String describeReviewer(Optional<String> reviewerId) {
        return reviewerId.orElse("none");
    }
}
