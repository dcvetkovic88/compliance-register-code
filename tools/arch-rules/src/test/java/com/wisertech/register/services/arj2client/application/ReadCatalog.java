package com.wisertech.register.services.arj2client.application;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/** Calls the catalog over HTTP itself instead of through a CatalogPort. */
public final class ReadCatalog {
    private final HttpClient client;

    public ReadCatalog(HttpClient client) {
        this.client = client;
    }

    public String readObligations(URI catalog) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(catalog).GET().build();
        return client.send(request, HttpResponse.BodyHandlers.ofString()).body();
    }
}
