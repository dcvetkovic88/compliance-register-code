package com.wisertech.register.services.arj12.application;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;

public final class RejectRequest {
    public ProblemDetail rejectRequest(String requestId) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, requestId);
    }
}
