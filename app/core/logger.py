import logging


def setup_logging():
    """
    Configures logging for the application.
    In a production setup, you might integrate with external logging aggregators.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging is set up!")
