"""The composition root: the only module that wires the API to the adapters."""

from app.adapters import persistence
from app.adapters.identity import tokens
from app.api import routes

WIRING = (routes, persistence, tokens)
