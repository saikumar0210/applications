# Policy Service

## Overview

Policy Service is a demo insurance application used to generate
application logs for the AMS Monitoring Connector.

The application simulates various policy operations including:

- Policy Creation
- Customer Validation
- Premium Calculation
- Policy Reconciliation

The generated logs are collected by New Relic and later consumed by the AMS Monitoring Connector for incident creation.

---

## Run

```bash
pip install -r requirements.txt

python application/app.py
```

---

## Flow

```
Policy Service

↓

Python Logger

↓

New Relic Agent

↓

New Relic

↓

AMS Monitoring Connector

↓

ServiceNow
```