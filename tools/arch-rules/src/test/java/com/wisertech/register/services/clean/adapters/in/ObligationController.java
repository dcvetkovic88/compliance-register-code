package com.wisertech.register.services.clean.adapters.in;

import com.wisertech.register.services.clean.application.ListObligations;
import com.wisertech.register.services.clean.domain.Obligation;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;

/** Serves the obligations of one regulation version. */
public final class ObligationController {
    private final ListObligations listObligations;

    public ObligationController(ListObligations listObligations) {
        this.listObligations = listObligations;
    }

    /** The obligations, or a problem response when the version is unknown. */
    public Object showObligations(String regulationVersion) {
        List<Obligation> obligations = listObligations.listObligations(regulationVersion);
        if (obligations.isEmpty()) {
            return ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        }
        return obligations;
    }
}
