package com.wisertech.register.services.arj2impl.application;

import com.wisertech.register.services.arj2impl.domain.AuditPort;
import java.util.ArrayList;
import java.util.List;

public final class DirectAudit implements AuditPort {
    private final List<String> eventIds = new ArrayList<>();

    @Override
    public void recordEvent(String eventId) {
        eventIds.add(eventId);
    }
}
