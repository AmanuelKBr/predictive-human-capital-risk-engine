# Gold Layer - Power BI Semantic Model (Star Schema)

PHCORE has no separate Gold notebook/table set. The "Gold layer" is the
semantic model itself: Silver Delta tables loaded into
`Predictive Human Capital Risk Engine Dashboard.pbix`, related into a star
schema, with DAX measures (`dax_measures.md`) and RLS (`rls_roles.md`)
layered on top. This model definition is preserved in the `.pbix` file
even after the Direct Lake data connection stops resolving.

---

## Dim_Date (calculated table)

```dax
Dim_Date =
ADDCOLUMNS (
    CALENDAR (DATE(2015, 1, 1), DATE(2030, 12, 31)),
    "Year", YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month Name", FORMAT([Date], "MMMM"),
    "Month Short", FORMAT([Date], "MMM"),
    "Quarter", "Q" & QUARTER([Date]),
    "Year-Month", FORMAT([Date], "YYYY-MM"),
    "Day of Week", WEEKDAY([Date]),
    "Day Name", FORMAT([Date], "dddd")
)
```

## Relationships

| From | To | Cardinality | Active? |
|---|---|---|---|
| `Dim_Date[Date]` | `silver_sessions[start_timestamp]` | 1:many | Active |
| `Dim_Date[Date]` | `silver_monthly_performance[report_month]` | 1:many | Active |
| `Dim_Date[Date]` | `silver_employees[hire_date]` | 1:many | **Inactive** - activated via `USERELATIONSHIP` (e.g. `90-Day Separation Rate`, `Total New Hires`, `Avg Training Hours (Retained)`) |
| `silver_employees[branch_id]` | `silver_branches[branch_id]` | many:1 | Active |
| `silver_sessions[course_id]` | `silver_courses[course_id]` | many:1 | Active |
| `silver_enrollments[session_id]` | `silver_sessions[session_id]` | many:1 | Active |
| `silver_enrollments[employee_id]` | `silver_employees[employee_id]` | many:1 | Active |
| `silver_evaluations[enrollment_id]` | `silver_enrollments[enrollment_id]` | many:1 | Active |
| `silver_certifications[employee_id]` | `silver_employees[employee_id]` | many:1 | Active |
| `silver_certifications[course_id]` | `silver_courses[course_id]` | many:1 | Active |

## Star schema shape

- **Fact tables**: `silver_sessions`, `silver_enrollments`, `silver_evaluations`,
  `silver_monthly_performance`, `silver_certifications`
- **Dimension tables**: `Dim_Date`, `silver_employees`, `silver_branches`,
  `silver_courses`
- `silver_employees` doubles as both a dimension (joined to enrollments,
  certifications) and a fact-like table for HR metrics (hire/termination
  dates, hourly_rate), related to `Dim_Date` via the inactive
  `hire_date` relationship for hiring/attrition time intelligence.
