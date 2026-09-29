# Vireo Audio Refund Intelligence

A local, deterministic Streamlit dashboard for reconciling refund-associated support tickets and investigating records that merit human review. It does not approve refunds or assess employee performance. No API key or paid service is used.

## Actual supplied inputs inspected

Inputs remain in this project root; do not move or overwrite them. The source pack contains `tickets.csv` (12,238 rows; 21 columns), `agents.csv` (44 roster records), `orders.csv` (15,000), `customers.csv` (9,500), `products.csv` (14), `support-policy.pdf` (2 pages), `email-thread.txt`, and `readme.txt`. No `submission-form.md` was supplied. The ticket export spans 2025-01-01 through 2026-06-30 and includes 21 fields: identifiers, timestamps, status/channel, customer/order/product/agent references, category, team, transfer count, CSAT, refund amount/reason, replacement indicator, message/notes, and source system. See the source `readme.txt` for field descriptions.

There are 638 duplicated ticket IDs (1,276 ticket source rows); duplicate representations commonly occur under both `helpdesk` and `legacy_fd`. The policy says the current helpdesk stores rupees while legacy Freshdesk values use a different native unit; the unit/conversion is not documented. The app picks the helpdesk representation for a duplicate ticket ID, retains legacy-only records for investigation, and excludes legacy amounts from INR totals. It does not infer a conversion factor. Raw values remain in `refund_amount_raw` and can be inspected with source system.

## Setup (Windows PowerShell)

```powershell
cd D:\Proj
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m streamlit run app.py`. Run tests with `python -m pytest -q`.

## Views and calculation definitions

- **Executive overview:** comparable refund amount, refund-associated unique ticket count, average per refund-associated ticket, and refund-ticket rate. Rate denominator is all unique tickets in the selected population.
- **Monthly trends:** sum of eligible ticket-level INR refund values and unique ticket counts by ticket creation calendar month; MoM delta and percentage are omitted for the first month and percentage is omitted when prior amount is zero.
- **Reasons / Agents:** deterministic sum, unique refund-ticket count, and average by recorded reason or resolving agent. Original code is preserved. Agent comparisons require context: Returns Desk processes most refunds by design; roster team and case mix are shown where present; Tier 2 is not comparable with Tier 1 under policy.
- **Review flags:** rule text and evidence are displayed per ticket. A ticket flagged for refund plus replacement requires order-level confirmation because the policy rule applies to the same order. Refund exceeding matched order value is a reconciliation prompt, not proof of error.
- **Ticket explorer:** search and CSV export over the currently filtered, one-row-per-ticket data.
- **Data quality:** source row / unique ID counts, legacy exclusions, missing dates, unmatched joins, and independent monthly/reason/agent reconciliations.

Amounts are parsed numerically; malformed and missing amounts remain missing and are excluded rather than treated as zero. Zero/negative amounts remain eligible only for `helpdesk` and are visible in data-quality reporting; negative values receive a review flag. No distinct payment transaction identifier exists, so the application reports refund-associated tickets, not transactions. Explicit order IDs are joined to orders; where an order ID is absent, the app fills it only if the customer + product SKU identifies exactly one order. Ambiguous fallback matches remain unmatched. Product, customer and agent dimensions are joined using source keys. Duplicate IDs use the helpdesk row where available; source rows are not modified. Duplicate dimension keys use the first row for joins, but source tables and their duplicate diagnostics remain visible.

The policy's documented checks are: refund and replacement for the same order is prohibited and should be escalated same day; goodwill credits are capped at ₹500 per ticket and need Team Lead approval; refund reason meanings and team roles are described in the PDF. This source export does not identify goodwill *credits* separately from refund amounts or expose approval status, so no cap breach/approval flag is asserted. Policy also lists automatic ₹350 store credits for response SLA misses; these are not represented as refund amounts and are not included. No narrative-versus-code classifier or LLM integration is included; core results remain local and deterministic.

## Verified initial data findings

The inspected raw export has 1,690 helpdesk refund rows totaling ₹4,817,881 before ticket-ID deduplication. It also has 775 legacy refund rows whose raw numeric sum is 225,306,200 in an undocumented legacy unit; that number is not INR-comparable and is not reported as rupees. Final comparable totals must be read from the app, which deduplicates ticket IDs and prefers helpdesk rows. These source counts are record counts, not payment transaction counts. Paired examples show legacy values ten times a helpdesk counterpart, but that pattern alone is insufficient to declare a universal conversion or apply it to legacy-only records.

## Privacy, limitations and troubleshooting

All processing occurs locally. Ticket messages and customer names remain in local source files and are not sent externally. The optional AI classifier is intentionally omitted; `.env.example` documents that no key is needed. Do not publish exported ticket data without authorization. The app's flags support investigation and do not prove misconduct, preventability, or savings. Reporting policy v3.2 effective 1 April 2025 also covers pre-effective-date tickets, so users should confirm historical policy applicability. Agent records are one row per assignment; this export contains one row per agent, but the join preserves the source roster design.

If input files are missing, the loader reports required-file errors and tolerates missing optional dimensions. Check CSV headers against the source schema if a required-column error appears. If Streamlit does not open automatically, use the local URL printed by its command. Install requirements into the active virtual environment. The dashboard uses paths relative to `app.py`, so it can run from the project root without relocating source data.
