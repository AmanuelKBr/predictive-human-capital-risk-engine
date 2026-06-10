# Power BI Semantic Model - DAX Measures

Backup of DAX measures from `Predictive Human Capital Risk Engine Dashboard.pbix`
(Direct Lake semantic model). Preserved as text because the Direct Lake
connection to OneLake will stop resolving once the Fabric trial expires,
even though the .pbix file itself (definitions, layout, RLS) remains intact.

---

## 90-Day Separation Rate

```dax
90-Day Separation Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS(silver_employees),
        USERELATIONSHIP(Dim_Date[Date], silver_employees[hire_date]),
        silver_employees[status] = "Terminated",
        (silver_employees[termination_date] - silver_employees[hire_date]) <= 90
    ),
    CALCULATE(
        COUNTROWS(silver_employees),
        USERELATIONSHIP(Dim_Date[Date], silver_employees[hire_date])
    ),
    0
)
```

## Avg Training Hours (Retained)

```dax
Avg Training Hours (Retained) =
CALCULATE(
    AVERAGE(silver_courses[duration_hours]),
    silver_employees[status] = "Active",
    USERELATIONSHIP(Dim_Date[Date], silver_employees[hire_date])
)
```

## Avg Transaction Error Rate

```dax
Avg Transaction Error Rate =
AVERAGE(silver_monthly_performance[transaction_error_rate])
```

## Total New Hires

```dax
Total New Hires =
CALCULATE(
    COUNTROWS(silver_employees),
    USERELATIONSHIP(Dim_Date[Date], silver_employees[hire_date])
)
```

## Total Training Investment

```dax
Total Training Investment =
SUMX(
    silver_enrollments,
    RELATED(silver_courses[duration_hours]) * RELATED(silver_employees[hourly_rate])
)
```

## YoY Training Investment Change

```dax
YoY Training Investment Change =
DIVIDE(
    [Total Training Investment] - CALCULATE([Total Training Investment], SAMEPERIODLASTYEAR(Dim_Date[Date])),
    CALCULATE([Total Training Investment], SAMEPERIODLASTYEAR(Dim_Date[Date])),
    0
)
```

## Dynamic Executive Summary

```dax
Dynamic Executive Summary =
VAR CurrentInvestment = FORMAT([Total Training Investment], "$#,##0")
VAR NoShowVal = [No-Show Rate]
VAR NoShowText = FORMAT(NoShowVal, "0.0%")
VAR NoShowTrend = IF(NoShowVal > 0.12, "⚠️ HIGH: Bleeding overhead on empty seats.", "✅ HEALTHY: Attendance within tolerance.")
VAR ErrorVal = [Avg Transaction Error Rate]
VAR ErrorText = FORMAT(ErrorVal, "0.0%")
VAR ErrorTrend = IF(ErrorVal > 0.02, "⚠️ CRITICAL: Exceeds 2.0% risk threshold.", "✅ ON TRACK: Operating safely.")
VAR CrossVal = [Avg Cross-Sell Ratio]
VAR CrossText = FORMAT(CrossVal, "0.00")
VAR CrossTrend = IF(CrossVal < 0.20, "⚠️ LOW: Revenue generation lagging.", "✅ STRONG: Above standard baseline.")
VAR SepVal = [90-Day Separation Rate]
VAR SepText = FORMAT(SepVal, "0.0%")
VAR SepTrend = IF(SepVal > 0.15, "⚠️ HIGH FLIGHT RISK: Early attrition elevated.", "✅ STABLE: Retention holding.")
VAR TotalHires = FORMAT([Total New Hires], "#,##0")
VAR AvgHrsText = FORMAT([Avg Training Hours (Retained)], "0.0")
VAR B = UNICHAR(10)
VAR BB = UNICHAR(10) & UNICHAR(10)
RETURN
"📋 MASTER EXECUTIVE BRIEFING: RISK & HUMAN CAPITAL" & BB &
"💰 FINANCIAL & INVESTMENT SUMMARY" & B &
"• Capital Deployed: " & CurrentInvestment & B &
"• Training Waste (No-Shows): " & NoShowText & " — " & NoShowTrend & BB &
"⚠️ OPERATIONAL RISK & PERFORMANCE" & B &
"• Transaction Error Rate: " & ErrorText & " — " & ErrorTrend & B &
"• Cross-Sell Conversion: " & CrossText & " — " & CrossTrend & BB &
"👥 ATTRITION & WORKFORCE STABILITY" & B &
"• Cohort Size: " & TotalHires & " new hires evaluated." & B &
"• 90-Day Separation Rate: " & SepText & " — " & SepTrend & B &
"• Avg Training (Retained Hires): " & AvgHrsText & " hours."
```

> **Note:** This measure references `[No-Show Rate]` and `[Avg Cross-Sell Ratio]`,
> which were not separately captured in this backup. If they exist as their own
> measures in the model, copy their DAX from Model view and add them here too —
> without them, `Dynamic Executive Summary` won't evaluate if the .pbix is ever
> rebuilt from scratch.

---

## Relationships referenced by these measures

- `Dim_Date[Date]` <-> `silver_employees[hire_date]` (inactive relationship,
  activated via `USERELATIONSHIP` — used for hire-date-based time intelligence)
- `Dim_Date[Date]` <-> `silver_monthly_performance[report_month]` (implied active
  relationship for `SAMEPERIODLASTYEAR` to work on `Total Training Investment`,
  which is not itself date-filtered — confirm this relationship exists if
  rebuilding)
- `silver_enrollments` -> `silver_courses` and `silver_enrollments` -> `silver_employees`
  (many-to-one, required for `RELATED()` in `Total Training Investment`)
