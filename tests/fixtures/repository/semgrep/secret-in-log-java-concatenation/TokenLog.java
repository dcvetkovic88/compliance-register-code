class TokenLog {
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(TokenLog.class);

    void recordIssue(String token) {
        logger.info("token=" + token);
    }
}
