import logging

log = logging.getLogger(__name__)


def sign_in(user_name: str, password: str) -> None:
    log.info("sign in %s with %s", user_name, password)
