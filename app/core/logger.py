import logging
import sys


def setup_logging():
    """
    Configures logging for the application.
    Outputs logs to standard output. Includes timestamp, level, logger name, and message.
    In a production setup, consider using structured logging (e.g., JSON) and
    integrating with external logging aggregators (like Datadog, Splunk, ELK stack).
    """
    log_format = "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging configured with format: %s", log_format)
