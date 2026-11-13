package demo;

class Arrangements {
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(Arrangements.class);

    // TODO(#12) page large registers
    int countArrangements(java.util.List<String> arrangements) {
        int arrangementCount = arrangements.size();
        logger.info("token refreshed for {} arrangements", arrangementCount);
        return arrangementCount;
    }
}
