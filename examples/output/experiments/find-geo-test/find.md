# Finding the test in the data

Locations report.
August 1, 2026 - November 11, 2026.

## The answer

**Candidate 1:** cost stopped in Evanston; Oak Park; Skokie from 2026-10-22 to 2026-11-11 (21 days), and was still off when the file ends.
- Regions that kept spending, the candidate controls: Berwyn; Cicero; Des Plaines; Niles; Park Ridge.
- In that window, leads in the candidate regions ran -29.6% against the control regions, compared with before. This is a first look, not the readout.

If the person confirms it, read it with:

```
python3 scripts/readout.py daily ../../examples/exports/experiments/leads-by-city-by-day.csv --out OUTPUT --test "Evanston;Oak Park;Skokie" --control "Berwyn;Cicero;Des Plaines;Niles;Park Ridge" --during 2026-10-22:2026-11-11 --cost-report ../../examples/exports/experiments/cost-by-city-by-day.csv --inferred
```

## To confirm with the person

1. Are these the test regions and dates? If they remember a different length, use theirs: the readout compares it with the data.
2. Was every campaign off in those regions, or only some?
3. Did anything else change in those regions in that time?

## How the numbers were made

- A day counts as off when a region's cost is under 10% of its usual (median) spending day. A stop counts when it lasts 7 days or more after at least 14 days in the file.
- Regions whose stops start within 3 days of each other are one test. Control regions spent on at least 80% of the window's days.
- The outcome check is the test regions' share of the outcome in the window against before, relative to the controls. The readout gives the range and the verdict.

## What this did not cover

- Heavy up tests (cost rising) are not searched for.
- A stop can be a budget running out or a campaign paused for another reason. Only the person can say it was a test.
