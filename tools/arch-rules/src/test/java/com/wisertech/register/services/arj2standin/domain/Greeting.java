package com.wisertech.register.services.arj2standin.domain;

import com.wisertech.register.services.arj2standin.adapters.out.IdentityStandIn;

public final class Greeting {
    public String greetUser(String userId) {
        return "Hello " + new IdentityStandIn().findUserName(userId);
    }
}
