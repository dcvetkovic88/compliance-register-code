package com.wisertech.register.services.clean.application;

import com.wisertech.register.services.clean.domain.CatalogPort;
import com.wisertech.register.services.clean.domain.Obligation;
import java.util.List;

public final class ListObligations {
    private final CatalogPort catalog;

    public ListObligations(CatalogPort catalog) {
        this.catalog = catalog;
    }

    public List<Obligation> listObligations(String regulationVersion) {
        return catalog.listObligations(regulationVersion);
    }
}
