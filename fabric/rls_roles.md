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

## ⚠️ Schema dependency: `silver_employees[email]`

This rule references `silver_employees[email]`, but the source API
(`main.py`) has no `email` field, and the original Dataflow Gen2
`employees` transformation did not produce one. As written, this RLS rule
will fail (`LOOKUPVALUE` referencing a non-existent column) or return blank
for everyone.

**Fix applied to `dataflow_gen2_silver.md`** (2026-06-10): added a
`WithEmail` step to the `employees` query that derives a synthetic email as

```
firstname.lastname@phcorebank.com
```

(lowercased, spaces stripped). To activate this in the live Fabric
workspace:

1. Open `DF_Silver_PHCORE` -> `employees` query -> Advanced Editor.
2. Insert the `WithEmail` step shown in `dataflow_gen2_silver.md` (right
   after `NormalizeNulls`, before `Deduplicated`).
3. Update `Deduplicated` to read from `WithEmail` instead of
   `NormalizeNulls`.
4. Refresh the dataflow so `silver_employees` gains the `email` column.
5. In Power BI Desktop, refresh/reload the model so the new column is
   visible to the RLS expression (no DAX change needed - it already
   references `silver_employees[email]`).

## Testing the role

In Power BI Desktop: **Modeling -> View as -> [check the role] -> Other
user**, enter a synthetic email matching the format above for any employee
who is a `branch_manager_emp_id` for some branch (e.g. for an employee
named Jane Doe, use `jane.doe@phcorebank.com`). The report should then show
only that branch's data. To find a valid manager email, look up any
`silver_branches[branch_manager_emp_id]`, find the matching
`silver_employees` row, and apply the `firstname.lastname@phcorebank.com`
pattern.
