package com.wisertech.register.services.arj4keycloak.adapters.out.identity;

import org.keycloak.representations.AccessToken;

/** Reads the subject of a token. */
public final class TokenReader {
    /** The subject of the token. */
    public String readSubject(AccessToken token) {
        return token.toString();
    }
}
