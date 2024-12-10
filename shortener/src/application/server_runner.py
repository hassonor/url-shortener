import logging

import uvicorn
from interface.api import app

logger = logging.getLogger(__name__)


async def run_api_server(host: str = "0.0.0.0", port: int = 8001):
    """
    Run the FastAPI server using uvicorn.

    This function is awaited in the main event loop.
    If the server stops (due to signal or error), the control returns to caller.
    """
    logger.info(
        {
            "action": "run_api_server",
            "host": host,
            "port": port,
            "message": f"Starting FastAPI server on {host}:{port}",
        }
    )

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    logger.info(
        {
            "action": "run_api_server",
            "status": "stopped",
            "message": "FastAPI server has stopped serving requests.",
        }
    )
