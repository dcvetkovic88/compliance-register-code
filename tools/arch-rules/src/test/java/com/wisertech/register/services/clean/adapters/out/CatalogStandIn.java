package com.wisertech.register.services.clean.adapters.out;

import com.wisertech.register.services.clean.domain.CatalogPort;
import com.wisertech.register.services.clean.domain.Obligation;
import java.util.List;
import java.util.Optional;

/** Stand-in catalog that holds its obligations in memory. */
public final class CatalogStandIn implements CatalogPort {
    private final List<Obligation> obligations;

    public CatalogStandIn(List<Obligation> obligations) {
        this.obligations = List.copyOf(obligations);
    }

    @Override
    public List<Obligation> listObligations(String regulationVersion) {
        return obligations.stream()
                .filter(obligation -> obligation.regulationVersion().equals(regulationVersion))
                .toList();
    }

    @Override
    public Optional<Obligation> findObligation(String obligationId) {
        return obligations.stream()
                .filter(obligation -> obligation.obligationId().equals(obligationId))
                .findFirst();
    }
}
