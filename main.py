from fastapi import FastAPI
from faker import Faker
import random
from datetime import datetime, timedelta

app = FastAPI(title="PHCORE Synthetic API", version="1.0")
fake = Faker()

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
        
        # Ensure every branch has a manager for RLS later
        if emp["job_title"] == "Branch Manager" and "manager_emp_id" not in branch:
            branch["branch_manager_emp_id"] = emp["employee_id"]

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

    # 4. Generate Sessions (Linked to Courses)
    for i in range(1, 201):
        course = random.choice(db["courses"])
        start_time = fake.date_time_between(start_date='-1y', end_date='+1m')
        db["sessions"].append({
            "session_id": f"SES-{i:04d}",
            "course_id": course["course_id"],
            "start_timestamp": start_time.isoformat(),
            "facility_cost": round(random.uniform(0, 1500), 2) if course["delivery_method"] == "In-Person" else 0.0,
            "max_capacity": random.choice([15, 30, 50, 100])
        })

    # 5. Generate Enrollments, Evaluations, and Performance Fact Data
    for i in range(1, 3001):
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

    # 6. Generate Monthly Performance (To correlate with L&D)
    for emp in db["employees"]:
        if emp["status"] == "Active":
            db["monthly_performance"].append({
                "perf_id": fake.uuid4(),
                "employee_id": emp["employee_id"],
                "report_month": "2026-05-01",
                "transaction_error_rate": round(random.uniform(0.01, 0.08), 3),
                "cross_sell_ratio": round(random.uniform(0.1, 0.5), 2),
                "customer_sat_score": round(random.uniform(70.0, 100.0), 1)
            })

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