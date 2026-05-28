"""
main.py — Application composition root.

Loads settings, configures logging, creates the FastAPI app via the factory,
and starts the uvicorn server.  This is the single entry point for the
entire application.
"""

import logging

import uvicorn

from adapters.inbound.fastapi.app import create_app
from core.config import get_settings


def main() -> None:
    settings = get_settings()

    # Configure root logging BEFORE starting the server
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    logger = logging.getLogger(__name__)
    logger.info(
        "Starting server on %s:%s (debug=%s)",
        settings.server.host,
        settings.server.port,
        settings.server.debug,
    )

    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
    )


# The module-level `app` object is referenced by uvicorn's "main:app" string.
# It MUST be created at import time so that `uvicorn.run("main:app", ...)`
# can resolve it.
app = create_app(get_settings())


if __name__ == "__main__":
    main()
