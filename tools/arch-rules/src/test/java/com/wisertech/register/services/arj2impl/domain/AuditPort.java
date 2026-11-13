package com.wisertech.register.services.arj2impl.domain;

/** Writes audit events. */
public interface AuditPort {
    void recordEvent(String eventId);
}
