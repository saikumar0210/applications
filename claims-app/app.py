"""
claims-app/app.py

Motor Insurance Claim Form — submits a claim and sends logs to New Relic via the AMS Monitoring Connector.
"""
import re
import uvicorn
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from nr_logger import Logger

app = FastAPI(title="Motor Insurance Claim Form")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


BACKEND_ERRORS = [
    {"code": "DB_CONNECTION_TIMEOUT", "message": "DatabaseConnectionTimeoutError: connection timed out while saving claim record | service=claims-db | host=db.internal | operation=INSERT | table=claims | timeout=30s | claim_ref=pending"},
    {"code": "DB_POOL_EXHAUSTED", "message": "DatabasePoolExhaustedError: DB connection pool exhausted — max connections reached | service=claims-db | host=db.internal | pool_size=20 | active_connections=20 | queued_requests=15 | wait_timeout=30s"},
    {"code": "TRANSACTION_ROLLBACK", "message": "TransactionRollbackError: failed to commit claim record — transaction rolled back | service=claims-db | host=db.internal | operation=COMMIT | table=claims | reason=deadlock detected | retry_attempts=3"},
]

_error_index = 0


def simulate_backend_error(claim_data: dict):
    global _error_index
    error = BACKEND_ERRORS[_error_index % len(BACKEND_ERRORS)]
    _error_index += 1
    return error


def print_log(level: str, event: str, data: dict):
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  LEVEL     : {level}")
    print(f"  EVENT     : {event}")
    print(f"  TIMESTAMP : {date.today().isoformat()}")
    print(f"  SERVICE   : claims-service")
    print(f"------- CLAIM DATA -------")
    for key, value in data.items():
        if key != "errors" and key != "error_code":
            print(f"  {key:<30}: {value}")
    if "errors" in data:
        print(f"------- ERRORS -------")
        for err in data["errors"]:
            print(f"  ❌ {err}")
    if "error_code" in data:
        print(f"------- ERROR CODE -------")
        print(f"  {data['error_code']}")
    print(f"{separator}\n")


def validate_claim(data: dict) -> list:
    errors = []

    if not re.fullmatch(r"POL-[0-9]{6}", data.get("policy_no", "")):
        errors.append("Policy No must follow format POL-XXXXXX (e.g. POL-123456)")

    if not re.fullmatch(r"CLM-[0-9]{6}", data.get("claim_no", "")):
        errors.append("Claim No must follow format CLM-XXXXXX (e.g. CLM-123456)")

    if not re.fullmatch(r"[A-Za-z ]{2,50}", data.get("insured_name", "")):
        errors.append("Insured Name must be letters and spaces only (2-50 characters)")

    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", data.get("email", "")):
        errors.append("E-Mail Id is invalid")

    if not re.fullmatch(r"[0-9]{10}", data.get("mobile_no", "")):
        errors.append("Mobile No must be 10 digits")

    if not data.get("accident_datetime"):
        errors.append("Date & Time of Accident is required")

    if not data.get("place_of_loss", "").strip():
        errors.append("Place of Loss is required")

    if not data.get("loss_type"):
        errors.append("Type of Loss must be selected")

    if len(data.get("accident_description", "").strip()) < 10:
        errors.append("Accident Description must be at least 10 characters")

    try:
        cost = float(data.get("estimated_cost", 0))
        if cost < 1:
            errors.append("Estimated Cost of Repairs must be at least $1")
    except ValueError:
        errors.append("Estimated Cost of Repairs must be a valid number")

    if not re.fullmatch(r"[A-Za-z ]{2,50}", data.get("driver_name", "")):
        errors.append("Driver Name must be letters and spaces only (2-50 characters)")

    try:
        age = int(data.get("driver_age", 0))
        if age < 18 or age > 100:
            errors.append("Driver Age must be between 18 and 100")
    except ValueError:
        errors.append("Driver Age must be a valid number")

    if not data.get("driver_type"):
        errors.append("Driver type (Owner/Paid Driver/Relative/Friend) must be selected")

    if not data.get("license_no", "").strip():
        errors.append("Driving License No is required")

    try:
        license_date = date.fromisoformat(data.get("license_valid_upto", ""))
        if license_date < date.today():
            errors.append("Driving License is expired")
    except ValueError:
        errors.append("Driving License Valid Up to date is invalid")

    return errors


@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("claims_form.html", {"request": request, "result": None})


@app.post("/submit", response_class=HTMLResponse)
def submit_claim(
    request: Request,
    policy_no: str = Form(default=""),
    claim_no: str = Form(default=""),
    vehicle_no: str = Form(default=""),
    engine_no: str = Form(default=""),
    chassis_no: str = Form(default=""),
    insured_name: str = Form(default=""),
    insured_address: str = Form(default=""),
    mobile_no: str = Form(default=""),
    email: str = Form(default=""),
    other_policies: str = Form(default=""),
    accident_datetime: str = Form(default=""),
    place_of_loss: str = Form(default=""),
    estimated_cost: str = Form(default=""),
    loss_type: List[str] = Form(default=[]),
    accident_description: str = Form(default=""),
    driver_name: str = Form(default=""),
    driver_age: str = Form(default=""),
    driver_type: str = Form(default=""),
    license_no: str = Form(default=""),
    license_valid_upto: str = Form(default=""),
    authorised_to_drive: str = Form(default=""),
    issuing_authority: str = Form(default=""),
    permit_no: str = Form(default=""),
    permit_valid_upto: str = Form(default=""),
    permit_issuing_authority: str = Form(default=""),
    fitness_valid_upto: str = Form(default=""),
    passengers_carried: str = Form(default=""),
    goods_carried: str = Form(default=""),
    gr_lr_no: str = Form(default=""),
    police_report_lodged: str = Form(default=""),
    fir_no: str = Form(default=""),
    police_station: str = Form(default=""),
    death_injury: str = Form(default=""),
    injury_details: str = Form(default=""),
):
    claim_data = {
        "policy_no": policy_no, "claim_no": claim_no, "vehicle_no": vehicle_no,
        "engine_no": engine_no, "chassis_no": chassis_no, "insured_name": insured_name,
        "insured_address": insured_address, "mobile_no": mobile_no, "email": email,
        "other_policies": other_policies, "accident_datetime": accident_datetime,
        "place_of_loss": place_of_loss, "estimated_cost": estimated_cost,
        "loss_type": loss_type, "accident_description": accident_description,
        "driver_name": driver_name, "driver_age": driver_age, "driver_type": driver_type,
        "license_no": license_no, "license_valid_upto": license_valid_upto,
        "authorised_to_drive": authorised_to_drive, "issuing_authority": issuing_authority,
        "permit_no": permit_no, "permit_valid_upto": permit_valid_upto,
        "permit_issuing_authority": permit_issuing_authority, "fitness_valid_upto": fitness_valid_upto,
        "passengers_carried": passengers_carried, "goods_carried": goods_carried,
        "gr_lr_no": gr_lr_no, "police_report_lodged": police_report_lodged,
        "fir_no": fir_no, "police_station": police_station,
        "death_injury": death_injury, "injury_details": injury_details,
    }

    errors = validate_claim(claim_data)

    if errors:
        try:
            Logger.error("claims-service", f"Claim validation failed | insured={insured_name} | policy={policy_no} | errors={errors}", {**claim_data, "errors": errors})
            print_log("ERROR", f"Claim validation failed | insured={insured_name} | policy={policy_no}", {**claim_data, "errors": errors})
        except Exception as e:
            print_log("ERROR", "Failed to publish error log to New Relic", {"exception": f"{type(e).__name__}: {e}"})
        return templates.TemplateResponse("claims_form.html", {
            "request": request,
            "result": {"success": False, "errors": errors, "claim": claim_data}
        })

    backend_error = simulate_backend_error(claim_data)
    if backend_error:
        try:
            Logger.error("claims-service", backend_error["message"], {**claim_data, "error_code": backend_error["code"]})
            print_log("ERROR", backend_error["message"], {**claim_data, "error_code": backend_error["code"]})
        except Exception as e:
            print_log("ERROR", "Failed to publish error log to New Relic", {"exception": f"{type(e).__name__}: {e}"})
        return templates.TemplateResponse("claims_form.html", {
            "request": request,
            "result": {"success": False, "errors": [backend_error["message"]], "claim": claim_data}
        })

    try:
        Logger.info("claims-service", f"Claim submitted successfully by {insured_name}", claim_data)
        print_log("INFO", f"Claim submitted successfully by {insured_name}", claim_data)
        log_status = True
    except Exception as e:
        print_log("ERROR", "Failed to publish info log to New Relic", {"exception": f"{type(e).__name__}: {e}"})
        log_status = False

    return templates.TemplateResponse("claims_form.html", {
        "request": request,
        "result": {"success": log_status, "claim": claim_data}
    })


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
