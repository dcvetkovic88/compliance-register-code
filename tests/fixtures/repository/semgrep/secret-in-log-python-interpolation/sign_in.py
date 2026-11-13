import logging


def sign_in(user_name: str, token: str) -> None:
    logging.info(f"sign in {user_name} with token={token}")
