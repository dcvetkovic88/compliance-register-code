package com.wisertech.register.services.arj2standin.adapters.out;

import com.wisertech.register.services.arj2standin.domain.IdentityPort;

/** Stand-in identity provider that knows one user. */
public final class IdentityStandIn implements IdentityPort {
    @Override
    public String findUserName(String userId) {
        return "user " + userId;
    }
}
