package com.wisertech.register.services.arj4identity.application.identity;

import com.nimbusds.jwt.SignedJwt;

/** Reads the session of a signed token outside the identity adapter. */
public final class SessionTokens {
    /** The session of the token. */
    public String readSession(SignedJwt token) {
        return token.toString();
    }
}
