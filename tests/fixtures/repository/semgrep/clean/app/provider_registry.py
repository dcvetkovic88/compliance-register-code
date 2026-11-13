import time


class ProviderRegistry:
    def wait_for_provider(self, timeout_seconds: float) -> None:
        time.sleep(timeout_seconds)
