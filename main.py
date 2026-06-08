from fastapi import FastAPI
from faker import Faker
import random
from datetime import datetime, timedelta

app = FastAPI(title="PHCORE Synthetic API", version="1.0")
fake = Faker()
Faker.seed(42)
random.seed(42)

# In-Memory Database to maintain Relational Integrity
db = {
    "branches": [], "employees": [], "courses": [], "sessions": [],
    "enrollments": [], "certifications": [], "evaluations": [], "monthly_performance": []
}

def generate_mock_data():
    print("Generating PHCORE Enterprise Data...")
    
    # 1. Generate Branches
    regions = ["Northeast", "Southeast", "Midwest", "West"]
    for i in range(1, 21):
        db["branches"].append({
            "branch_id": f"BR-{i:03d}",
            "branch_name": f"{fake.city()} Branch",
            "region": random.choice(regions),
            "state": fake.state_abbr(),
            "cost_center_code": f"CC-{fake.bothify(text='####')}"
        })

    # 2. Generate Employees (Linked to Branches)
    departments = ["Retail Banking", "Wealth Management", "Commercial Lending", "Back-Office Ops"]
    job_titles = ["Teller", "Loan Officer", "Branch Manager", "Analyst", "Customer Service Rep"]
    for i in range(1, 501):
        branch = random.choice(db["branches"])
        is_terminated = random.choice([True, False, False, False]) # 25% turnover rate
        hire_date = fake.date_between(start_date='-5y', end_date='-6m')
        
        emp = {
            "employee_id": f"EMP-{i:05d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "branch_id": branch["branch_id"],
            "department": random.choice(departments),
            "job_title": random.choice(job_titles),
            "hourly_rate": round(random.uniform(20.0, 65.0), 2),
            "hire_date": hire_date.isoformat(),
            "status": "Terminated" if is_terminated else "Active",
            "termination_date": fake.date_between(start_date=hire_date, end_date='today').isoformat() if is_terminated else None
        }
        db["employees"].append(emp)

    # Guarantee every branch has exactly one branch_manager_emp_id (required for Power BI dynamic RLS)
    for branch in db["branches"]:
        branch_employees = [e for e in db["employees"] if e["branch_id"] == branch["branch_id"]]
        managers = [e for e in branch_employees if e["job_title"] == "Branch Manager"]
        if managers:
            chosen = managers[0]
        else:
            chosen = random.choice(branch_employees)
            chosen["job_title"] = "Branch Manager"
        branch["branch_manager_emp_id"] = chosen["employee_id"]

    # 3. Generate Courses
    course_categories = ["Regulatory/Compliance", "Leadership", "Systems/Tech", "Soft Skills"]
    for i in range(1, 31):
        db["courses"].append({
            "course_id": f"CRS-{i:03d}",
            "course_name": fake.catch_phrase().title() + " Training",
            "category": random.choice(course_categories),
            "delivery_method": random.choice(["vILT", "eLearning", "In-Person"]),
            "duration_hours": random.choice([1.0, 2.0, 4.0, 8.0]),
            "is_mandatory": random.choice([True, False])
        })

    # 4. Generate Sessions (Linked to Courses) - spans 3 years so L&D volume/spend can be compared YoY
    for i in range(1, 601):
        course = random.choice(db["courses"])
        start_time = fake.date_time_between(start_date='-3y', end_date='+1m')
        db["sessions"].append({
            "session_id": f"SES-{i:04d}",
            "course_id": course["course_id"],
            "start_timestamp": start_time.isoformat(),
            "facility_cost": round(random.uniform(0, 1500), 2) if course["delivery_method"] == "In-Person" else 0.0,
            "max_capacity": random.choice([15, 30, 50, 100])
        })

    # 5. Generate Enrollments, Evaluations, and Performance Fact Data (3x volume to match the 3-year session span)
    for i in range(1, 9001):
        emp = random.choice(db["employees"])
        session = random.choice(db["sessions"])
        status = random.choice(["Attended", "Attended", "Attended", "No-Show", "Waitlisted"])
        
        enrollment_id = f"ENR-{i:06d}"
        db["enrollments"].append({
            "enrollment_id": enrollment_id,
            "session_id": session["session_id"],
            "employee_id": emp["employee_id"],
            "status": status
        })

        # Generate Evaluation only if Attended
        if status == "Attended":
            db["evaluations"].append({
                "eval_id": f"EVL-{i:06d}",
                "enrollment_id": enrollment_id,
                "knowledge_test_score": round(random.uniform(65.0, 100.0), 1),
                "nps_score": random.randint(1, 10)
            })

    # 6. Generate Monthly Performance - a full 3-year history aligned to each employee's actual tenure.
    # Active employees report through the current month; terminated employees report only up to their
    # termination month. This produces realistic YoY patterns (attrition, new-hire ramp-up) for DAX/visuals.
    PERF_WINDOW_START = datetime(2023, 7, 1).date()
    PERF_WINDOW_END = datetime(2026, 6, 1).date()

    def month_sequence(start, end):
        months = []
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            months.append(f"{y}-{m:02d}-01")
            m += 1
            if m == 13:
                m, y = 1, y + 1
        return months

    perf_counter = 1
    for emp in db["employees"]:
        hire_date = datetime.fromisoformat(emp["hire_date"]).date()
        term_date = datetime.fromisoformat(emp["termination_date"]).date() if emp["termination_date"] else None
        record_start = max(hire_date, PERF_WINDOW_START)
        record_end = min(term_date, PERF_WINDOW_END) if term_date else PERF_WINDOW_END
        if record_start > record_end:
            continue
        for report_month in month_sequence(record_start, record_end):
            db["monthly_performance"].append({
                "perf_id": f"PRF-{perf_counter:06d}",
                "employee_id": emp["employee_id"],
                "report_month": report_month,
                "transaction_error_rate": round(random.uniform(0.01, 0.08), 3),
                "cross_sell_ratio": round(random.uniform(0.1, 0.5), 2),
                "customer_sat_score": round(random.uniform(70.0, 100.0), 1)
            })
            perf_counter += 1

    # 7. Generate Certifications (Compliance Fact - linked to Regulatory/Compliance courses)
    license_names = ["BSA/AML Certification", "NMLS Mortgage License", "Series 6", "Series 7", "CRCM Compliance Manager"]
    regulatory_courses = [c for c in db["courses"] if c["category"] == "Regulatory/Compliance"] or db["courses"]
    today = datetime.now().date()
    cert_counter = 1
    for emp in db["employees"]:
        if emp["status"] != "Active":
            continue
        hire_date = datetime.fromisoformat(emp["hire_date"]).date()
        for _ in range(random.randint(0, 2)):
            course = random.choice(regulatory_courses)
            issue_date = fake.date_between(start_date='-3y', end_date='-1m')
            if issue_date < hire_date:
                issue_date = hire_date + timedelta(days=random.randint(30, 180))
            expiration_date = issue_date + timedelta(days=365 * random.choice([1, 2, 3]))
            days_to_expiry = (expiration_date - today).days
            if days_to_expiry < 0:
                status = "Expired"
            elif days_to_expiry <= 60:
                status = "Grace Period"
            else:
                status = "Active"
            db["certifications"].append({
                "cert_id": f"CRT-{cert_counter:05d}",
                "employee_id": emp["employee_id"],
                "course_id": course["course_id"],
                "license_name": random.choice(license_names),
                "issue_date": issue_date.isoformat(),
                "expiration_date": expiration_date.isoformat(),
                "status": status
            })
            cert_counter += 1

# Run data generation on startup
@app.on_event("startup")
async def startup_event():
    generate_mock_data()

# --- API Endpoints ---
@app.get("/branches")
def get_branches(): return db["branches"]

@app.get("/employees")
def get_employees(): return db["employees"]

@app.get("/courses")
def get_courses(): return db["courses"]

@app.get("/sessions")
def get_sessions(): return db["sessions"]

@app.get("/enrollments")
def get_enrollments(): return db["enrollments"]

@app.get("/evaluations")
def get_evaluations(): return db["evaluations"]

@app.get("/monthly_performance")
def get_performance(): return db["monthly_performance"]

@app.get("/certifications")
def get_certifications(): return db["certifications"]