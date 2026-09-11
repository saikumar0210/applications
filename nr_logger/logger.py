import os
from dotenv import load_dotenv

from nr_logger.models.log_event import LogEvent
from nr_logger.publisher import NewRelicPublisher

load_dotenv()

_publisher = NewRelicPublisher()
_app_name = os.getenv("APPLICATION_NAME", "Unknown Application")
_environment = os.getenv("ENVIRONMENT", "DEV")


class Logger:

    @staticmethod
    def info(service: str, message: str, details: dict | None = None):
        _publisher.publish(LogEvent(
            application=_app_name,
            service=service,
            environment=_environment,
            severity="INFO",
            message=message,
            additional_details=details or {}
        ))

    @staticmethod
    def warning(service: str, message: str, details: dict | None = None):
        _publisher.publish(LogEvent(
            application=_app_name,
            service=service,
            environment=_environment,
            severity="WARNING",
            message=message,
            additional_details=details or {}
        ))

    @staticmethod
    def error(service: str, message: str, details: dict | None = None):
        _publisher.publish(LogEvent(
            application=_app_name,
            service=service,
            environment=_environment,
            severity="ERROR",
            message=message,
            additional_details=details or {}
        ))
