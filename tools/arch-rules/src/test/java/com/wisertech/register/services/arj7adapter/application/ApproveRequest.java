package com.wisertech.register.services.arj7adapter.application;

import com.wisertech.register.services.arj7adapter.adapters.out.ApprovalStore;

public final class ApproveRequest {
    private final ApprovalStore store = new ApprovalStore();

    public String approveRequest(String requestId) {
        return store.saveApproval(requestId);
    }
}
