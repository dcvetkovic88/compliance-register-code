package com.wisertech.register.libs.arj6service;

import com.wisertech.register.services.arj6target.domain.Provider;

public final class ProviderNames {
    private ProviderNames() {}

    public static String nameProvider(Provider provider) {
        return provider.providerId();
    }
}
