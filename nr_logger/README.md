# nr_logger — Shared New Relic Logging Package

## Overview

`nr_logger` is a shared logging package that sends logs directly to New Relic Log API.
Any new application created under `C:\Sai\applications` can use this package to send logs to New Relic without writing any New Relic specific code.

---

## Package Structure

```
nr_logger/
├── __init__.py          ← Exposes Logger directly
├── logger.py            ← Logger class with info / warning / error methods
├── publisher.py         ← Sends logs to New Relic Log API
└── models/
    └── log_event.py     ← LogEvent Pydantic model
```

---

## How It Works

```
Your Application
      ↓
  Logger.info() / Logger.warning() / Logger.error()
      ↓
  NewRelicPublisher.publish()
      ↓
  New Relic Log API (https://log-api.newrelic.com/log/v1)
      ↓
  New Relic Dashboard
```

---

## Step-by-Step Integration Guide

### Step 1 — Create Your Application Folder

Create your new application folder inside `C:\Sai\applications\`.

```
C:\Sai\applications\
└── your-app\
    ├── app.py
    ├── .env
    └── requirements.txt
```

---

### Step 2 — Add New Relic Credentials to .env

Create a `.env` file in your application folder with the following variables.
`nr_logger` reads these automatically — no extra config needed.

```env
APPLICATION_NAME=Your App Name
ENVIRONMENT=DEV

NEW_RELIC_LICENSE_KEY=your_new_relic_license_key_here
NEW_RELIC_LOG_API=https://log-api.newrelic.com/log/v1
```

> `NEW_RELIC_LICENSE_KEY` — Found in New Relic under API Keys → License Key (INGEST type).
> `NEW_RELIC_LOG_API` — Default is `https://log-api.newrelic.com/log/v1`. No need to change unless you are on EU region, in which case use `https://log-api.eu.newrelic.com/log/v1`.

---

### Step 3 — Add Dependencies to requirements.txt

```txt
requests
pydantic
python-dotenv
```

---

### Step 4 — Add sys.path So nr_logger is Importable

Since `nr_logger` lives at `C:\Sai\applications\nr_logger`, Python needs to know where to find it.
Add this at the very top of your entry point file (e.g. `app.py`) before any `nr_logger` import.

```python
import sys
sys.path.insert(0, r"C:\Sai\applications")   # must be before nr_logger import

from nr_logger import Logger
```

> This is only needed in the entry point file (e.g. `app.py`). All other files in your app can just do `from nr_logger import Logger` directly once the path is set in `app.py`.

---

### Step 5 — Add a Console Logger (Optional but Recommended)

The `nr_logger` sends logs to New Relic but does not print to the console.
For local visibility during development, add a `shared/logger.py` in your app like the existing `policy_service` does.

```
your-app/
└── shared/
    └── logger.py
```

```python
# shared/logger.py

import logging
import sys


def get_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel("INFO")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
```

Use it alongside `nr_logger` in your service:

```python
from shared.logger import get_logger
from nr_logger import Logger

_logger = get_logger(__name__)   # prints to console


class YourService:

    def run(self):
        _logger.info("Service started")                          # console only
        Logger.info("your-service", "Service started")          # New Relic only
```

---

### Step 6 — Import and Use Logger in Your Application

#### Logger.info() — For normal successful operations

```python
Logger.info(
    service="your-service-name",
    message="Operation completed successfully",
    details={"key": "value"}               # optional extra data
)
```

#### Logger.warning() — For unexpected but non-critical situations

```python
Logger.warning(
    service="your-service-name",
    message="Retrying due to timeout",
    details={"attempt": 2}
)
```

#### Logger.error() — For failures and exceptions

```python
try:
    # your code
    pass
except Exception as ex:
    Logger.error(
        service="your-service-name",
        message="Operation failed",
        details={"exception": str(ex)}
    )
```

---

### Step 7 — Full Working Example

```python
# your-app/app.py

import sys
sys.path.append(r"C:\Sai\applications")

from nr_logger import Logger


class YourService:

    SERVICE_NAME = "your-service-name"

    def run(self):

        Logger.info(self.SERVICE_NAME, "Service started")

        try:
            # your business logic here
            result = self.do_something()
            Logger.info(self.SERVICE_NAME, "Task completed", {"result": result})

        except Exception as ex:
            Logger.error(self.SERVICE_NAME, "Task failed", {"exception": str(ex)})


    def do_something(self):
        return "success"


if __name__ == "__main__":
    service = YourService()
    service.run()
```

---

### Step 8 — How to Run Your Application

#### Plain Python App (like policy_service)

Always run from the application root folder, not from inside a subfolder.

```bash
cd C:\Sai\applications\policy_service
python application/app.py
```

#### FastAPI App (like claims-app)

```bash
cd C:\Sai\applications\claims-app
python app.py
```

Then open `http://localhost:9000` in your browser.

> Running from the correct folder ensures `.env` is loaded correctly and all relative imports resolve properly.

---

### Step 9 — Verify Logs in New Relic

1. Go to [New Relic](https://one.newrelic.com)
2. Navigate to **Logs** from the left menu
3. Search using your application name or service name:

```
application = "Your App Name"
```

or filter by severity:

```
severity = "ERROR"
```

---

## What Gets Sent to New Relic

Every log call sends the following fields to New Relic:

| Field | Description | Example |
|---|---|---|
| `application` | Loaded from `APPLICATION_NAME` in `.env` | `Claims App` |
| `service` | Passed by you in the Logger call | `claims-service` |
| `environment` | Loaded from `ENVIRONMENT` in `.env` | `DEV` |
| `severity` | Set by the method used | `INFO`, `WARNING`, `ERROR` |
| `message` | Passed by you in the Logger call | `Claim submitted` |
| `timestamp` | Auto-generated UTC timestamp | `2025-01-01T10:00:00` |
| `details` | Optional dict of extra data passed by you | `{"policyId": "POL-123"}` |

---

## Existing Applications Using nr_logger

| Application | Location |
|---|---|
| Policy Service | `C:\Sai\applications\policy_service` |
| Claims App | `C:\Sai\applications\claims-app` |

---

## Important Notes

- Do NOT modify `nr_logger` files when adding a new application — just import and use it.
- Each application manages its own `.env` file with its own `APPLICATION_NAME` and `NEW_RELIC_LICENSE_KEY`.
- Adding a new application has zero impact on existing applications.
