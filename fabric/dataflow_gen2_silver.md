# Silver Layer - Dataflow Gen2 (Power Query M)

Backup of the M code used in `DF_Silver_PHCORE` to transform Bronze raw JSON
(`Files/bronze/raw_json/<entity>/<entity>.json`) into Silver Delta tables
(`silver_<entity>`).

## Pattern

For each entity:
1. Get data -> Lakehouse -> `Files/bronze/raw_json/<entity>/<entity>.json`
2. In Advanced Editor, rename the last auto-generated step to `SourceJSON`
3. Replace `in SourceJSON` with the transformation block below
4. Set data destination -> Lakehouse table `silver_<entity>` (Replace)

---

## branches

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"branch_id","branch_name","region","state","cost_center_code","branch_manager_emp_id"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"branch_id", type text},{"branch_name", type text},{"region", type text},
        {"state", type text},{"cost_center_code", type text},{"branch_manager_emp_id", type text}
    }),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"branch_id", NormText, type text},{"branch_name", NormText, type text},
        {"region", NormText, type text},{"state", NormText, type text},
        {"cost_center_code", NormText, type text},{"branch_manager_emp_id", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"branch_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

## employees

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"employee_id","first_name","last_name","branch_id","department","job_title",
         "hourly_rate","hire_date","status","termination_date"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"employee_id", type text},{"first_name", type text},{"last_name", type text},
        {"branch_id", type text},{"department", type text},{"job_title", type text},
        {"hourly_rate", type number},{"hire_date", type date},
        {"status", type text},{"termination_date", type date}
    }, "en-US"),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"employee_id", NormText, type text},{"first_name", NormText, type text},
        {"last_name", NormText, type text},{"branch_id", NormText, type text},
        {"department", NormText, type text},{"job_title", NormText, type text},
        {"status", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"employee_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

> `termination_date` is null for Active employees - Power Query handles null
> correctly when casting to `type date`.

## courses

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"course_id","course_name","category","delivery_method","duration_hours","is_mandatory"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"course_id", type text},{"course_name", type text},{"category", type text},
        {"delivery_method", type text},{"duration_hours", type number},{"is_mandatory", type logical}
    }),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"course_id", NormText, type text},{"course_name", NormText, type text},
        {"category", NormText, type text},{"delivery_method", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"course_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

## sessions

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"session_id","course_id","start_timestamp","facility_cost","max_capacity"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"session_id", type text},{"course_id", type text},
        {"start_timestamp", type datetime},{"facility_cost", type number},{"max_capacity", Int64.Type}
    }, "en-US"),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"session_id", NormText, type text},{"course_id", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"session_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

> `start_timestamp` is cast to `type datetime` (not date) - `"en-US"` culture
> handles Faker's ISO-8601 strings including any optional fractional seconds.

## enrollments

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"enrollment_id","session_id","employee_id","status"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"enrollment_id", type text},{"session_id", type text},
        {"employee_id", type text},{"status", type text}
    }),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"enrollment_id", NormText, type text},{"session_id", NormText, type text},
        {"employee_id", NormText, type text},{"status", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"enrollment_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

## evaluations

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"eval_id","enrollment_id","knowledge_test_score","nps_score"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"eval_id", type text},{"enrollment_id", type text},
        {"knowledge_test_score", type number},{"nps_score", Int64.Type}
    }),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"eval_id", NormText, type text},{"enrollment_id", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"eval_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

## certifications

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"cert_id","employee_id","course_id","license_name","issue_date","expiration_date","status"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"cert_id", type text},{"employee_id", type text},{"course_id", type text},
        {"license_name", type text},{"issue_date", type date},
        {"expiration_date", type date},{"status", type text}
    }, "en-US"),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"cert_id", NormText, type text},{"employee_id", NormText, type text},
        {"course_id", NormText, type text},{"license_name", NormText, type text},
        {"status", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"cert_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```

## monthly_performance

```m
    NormText = (val) => if val = null then null else if Text.Trim(val) = "" then null else Text.Trim(val),
    AsTable = Table.FromList(SourceJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"perf_id","employee_id","report_month","transaction_error_rate","cross_sell_ratio","customer_sat_score"}),
    TypeEnforced = Table.TransformColumnTypes(Expanded, {
        {"perf_id", type text},{"employee_id", type text},{"report_month", type date},
        {"transaction_error_rate", type number},{"cross_sell_ratio", type number},
        {"customer_sat_score", type number}
    }, "en-US"),
    NormalizeNulls = Table.TransformColumns(TypeEnforced, {
        {"perf_id", NormText, type text},{"employee_id", NormText, type text}
    }),
    Deduplicated = Table.Distinct(NormalizeNulls, {"perf_id"}),
    WithLoadedAt = Table.AddColumn(Deduplicated, "_silver_loaded_at", each DateTime.LocalNow(), type datetime),
    WithSource = Table.AddColumn(WithLoadedAt, "_source_system", each "phcore_api", type text)
in
    WithSource
```
