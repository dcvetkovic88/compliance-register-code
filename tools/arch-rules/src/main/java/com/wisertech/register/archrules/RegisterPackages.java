package com.wisertech.register.archrules;

/**
 * The package layout the rules read (plan D2). A service lives in {@code com.wisertech.register.services.<service>}
 * with the packages {@code domain}, {@code application}, {@code adapters.in} and {@code adapters.out}; a library
 * lives in {@code com.wisertech.register.libs.<library>}.
 */
final class RegisterPackages {
    static final String REGISTER = "com.wisertech.register..";
    static final String SERVICES = "com.wisertech.register.services..";
    static final String SERVICE_SLICES = "com.wisertech.register.services.(*)..";
    static final String LIBS = "com.wisertech.register.libs..";
    static final String DOMAIN = "..domain..";
    static final String APPLICATION = "..application..";
    static final String ADAPTERS = "..adapters..";
    static final String ADAPTERS_IN = "..adapters.in..";
    static final String ADAPTERS_OUT = "..adapters.out..";
    static final String PERSISTENCE = "..adapters.out.persistence..";
    /** The identity adapter, inbound or outbound; an {@code identity} package outside the adapters is not it. */
    static final String IDENTITY = "..adapters.*.identity..";

    /** Spring, JDBC, servlet, HTTP client, JSON, JPA and Keycloak types, which the domain never names (AR-J0). */
    static final String[] FRAMEWORKS = {
        "org.springframework..",
        "java.sql..",
        "javax.sql..",
        "jakarta.servlet..",
        "javax.servlet..",
        "java.net.http..",
        "org.apache.hc..",
        "org.apache.http..",
        "okhttp3..",
        "com.fasterxml.jackson..",
        "tools.jackson..",
        "com.google.gson..",
        "jakarta.json..",
        "jakarta.persistence..",
        "javax.persistence..",
        "org.hibernate..",
        "org.keycloak.."
    };

    /**
     * HTTP, socket and remote call clients, with which a service reaches another suite capability; only
     * {@code adapters.out} names them, so the rest of the service reaches a capability through its port (AR-J2).
     */
    static final String[] REMOTE_CLIENTS = {
        "java.net.http..",
        "org.apache.hc..",
        "org.apache.http..",
        "okhttp3..",
        "org.springframework.web.client..",
        "org.springframework.web.reactive.function.client..",
        "org.springframework.web.service.invoker..",
        "org.springframework.cloud.openfeign..",
        "io.grpc..",
        "jakarta.ws.rs.client..",
        "javax.ws.rs.client.."
    };

    /** Remote call types of {@code java.net} itself, outside its {@code http} package (AR-J2). */
    static final String JAVA_NET_CLIENTS = "java\\.net\\.(HttpURLConnection|URLConnection|Socket|DatagramSocket)";

    /** JDBC and the PostgreSQL driver, only in the persistence adapter of a service (AR-J3). */
    static final String[] JDBC = {"java.sql..", "javax.sql..", "org.springframework.jdbc..", "org.postgresql.."};

    /** OAuth and token libraries, only in an identity adapter (AR-J4). */
    static final String[] TOKEN_LIBRARIES = {
        "com.nimbusds..", "io.jsonwebtoken..", "org.springframework.security.oauth2.."
    };

    /** RFC 9457 problem response types, only in {@code adapters.in} (AR-J12). */
    static final String PROBLEM_TYPES =
            "org\\.springframework\\.(http\\.ProblemDetail|web\\.ErrorResponse(Exception)?)";

    private RegisterPackages() {}
}
