package com.wisertech.register.fixture.adapters.out;

import com.wisertech.register.fixture.domain.CatalogPort;
import java.util.Map;
import java.util.Optional;

/** Stand-in catalog that holds its obligations in memory. */
public final class InMemoryCatalog implements CatalogPort {
    private final Map<String, String> titles;

    public InMemoryCatalog(Map<String, String> titles) {
        this.titles = Map.copyOf(titles);
    }

    @Override
    public Optional<String> findObligationTitle(String obligationId) {
        return Optional.ofNullable(titles.get(obligationId));
    }
}
