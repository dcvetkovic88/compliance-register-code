package com.wisertech.register.fixture.domain;

import java.util.Optional;

/** Reads the obligations of the regulation catalog. */
public interface CatalogPort {
    Optional<String> findObligationTitle(String obligationId);
}
