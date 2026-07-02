"""OpenTelemetry + Azure Monitor setup.

Instrumentation is best-effort: if the Application Insights connection string is
not configured, telemetry is skipped rather than blocking startup.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        logger.info("APPLICATIONINSIGHTS_CONNECTION_STRING not set; telemetry disabled.")
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        configure_azure_monitor()
        FastAPIInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        logger.info("Azure Monitor telemetry configured.")
    except Exception:  # noqa: BLE001 - telemetry must never crash the app
        logger.exception("Failed to configure telemetry; continuing without it.")
