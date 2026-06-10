# Power BI Semantic Model - Row-Level Security (RLS)

Backup of the dynamic RLS rule from `Predictive Human Capital Risk Engine
Dashboard.pbix` (Direct Lake semantic model).

---

## Role: Branch Manager (dynamic)

Table filter on `silver_branches`:

```dax
[branch_manager_emp_id] = LOOKUPVALUE(silver_employees[employee_id], silver_employees[email], USERPRINCIPALNAME())
```

How it works: when a user opens the report, `USERPRINCIPALNAME()` returns
their login (email/UPN). `LOOKUPVALUE` finds the matching row in
`silver_employees[email]` and returns that employee's `employee_id`. The
filter then keeps only the row in `silver_branches` where
`branch_manager_emp_id` equals that ID — and (via relationships)
everything related to that branch (its employees, sessions, enrollments,
performance, etc.).

---

## `silver_employees[email]` - synthetic column

`silver_employees[email]` does not come from the source API. It's derived
in the Dataflow Gen2 `employees` query (see `dataflow_gen2_silver.md`) as:

```
Text.Lower([first_name] & Text.From([employee_id]) & "@phcore.com")
```

i.e. `firstname` + `employee_id` + `@phcore.com`, all lowercase - e.g. for
employee `jane` with ID `EMP-00007`, the email is
`janeemp-00007@phcore.com`. This is already applied in the live
`DF_Silver_PHCORE` dataflow and `silver_employees` has the column.

## Testing the role

In Power BI Desktop: **Modeling -> View as -> [check the role] -> Other
user**, enter the synthetic email (per the format above) for any employee
who is a `branch_manager_emp_id` for some branch. The report should then
show only that branch's data. To find a valid manager email, look up any
`silver_branches[branch_manager_emp_id]`, find the matching
`silver_employees` row, and build `firstname` + `employee_id` +
`@phcore.com` (lowercase).
