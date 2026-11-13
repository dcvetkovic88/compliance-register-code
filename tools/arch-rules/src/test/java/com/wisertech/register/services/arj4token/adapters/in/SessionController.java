package com.wisertech.register.services.arj4token.adapters.in;

import com.nimbusds.jwt.SignedJwt;

/** Shows the session of a signed token. */
public final class SessionController {
    /** The session of the token. */
    public String showSession(SignedJwt token) {
        return token.toString();
    }
}
