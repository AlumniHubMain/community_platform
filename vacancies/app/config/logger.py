import picologging.config
from pythonjsonlogger.jsonlogger import JsonFormatter


def setup_logging():
    """
    Configure logging with a custom JSON formatter.
    """
    # Create handler
    console_handler = picologging.StreamHandler()
    console_handler.setLevel(picologging.INFO)

    # Create formatter
    formatter = JsonFormatter(
        fmt="%(asctime)s %(name)s %(module)s %(funcName)s %(lineno)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        rename_fields={"asctime": "timestamp", "levelname": "severity"},
    )

    # Set formatter on handler
    console_handler.setFormatter(formatter)

    # Get root logger and configure it
    root_logger = picologging.getLogger()
    root_logger.setLevel(picologging.INFO)
    root_logger.addHandler(console_handler)
