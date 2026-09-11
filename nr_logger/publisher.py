import os
import requests
from dotenv import load_dotenv

from nr_logger.models.log_event import LogEvent

load_dotenv()


class NewRelicPublisher:

    def __init__(self):
        self.url = os.getenv("NEW_RELIC_LOG_API", "https://log-api.newrelic.com/log/v1")
        self.headers = {
            "Api-Key": os.getenv("NEW_RELIC_LICENSE_KEY"),
            "Content-Type": "application/json"
        }

    def publish(self, event: LogEvent):
        payload = [{
            "application": event.application,
            "service": event.service,
            "environment": event.environment,
            "level": event.severity,
            "priority": "1" if event.severity == "ERROR" else "4",
            "message": event.message,
            "timestamp": event.timestamp.isoformat(),
            "details": event.additional_details
        }]

        response = requests.post(url=self.url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
