package com.wisertech.register.services.clean.domain;

import java.util.List;
import java.util.Optional;

/** Reads the obligations of the regulation catalog. */
public interface CatalogPort {
    List<Obligation> listObligations(String regulationVersion);

    Optional<Obligation> findObligation(String obligationId);
}
