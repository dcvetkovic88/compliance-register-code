package com.wisertech.register.services.arj10.adapters.in;

import java.time.Clock;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.annotation.Autowired;

/** Shows providers. */
public final class ProviderController {
    @Autowired
    private @Nullable Clock clock;

    /** Whether the clock was injected. */
    public boolean hasClock() {
        return clock != null;
    }
}
