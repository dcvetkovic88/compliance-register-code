package com.wisertech.register.services.arj2standin.domain;

/** Names the user behind a request. */
public interface IdentityPort {
    String findUserName(String userId);
}
