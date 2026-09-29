# Finance and Support Operations memo

**To:** Arjun Mehta, Finance Controller; Support Operations  
**Subject:** Vireo support refund reconciliation and review dashboard

## Business problem and work delivered

The supplied ticket export mixes current-helpdesk rupee values with legacy Freshdesk values in a different, undocumented unit, and contains repeated ticket IDs. This explains why a raw sum is not a defensible finance total. I built a local Streamlit dashboard that selects one record per ticket, prefers the current-helpdesk representation when duplicates exist, and presents deterministic monthly, reason, agent, product, ticket, and review-flag analysis with CSV export and reconciliation checks.

## Verified observations and limits

The source has 12,238 ticket rows and 11,600 unique ticket IDs. There are 638 duplicated ticket IDs represented in 1,276 source rows. After preferring helpdesk rows for duplicate IDs and excluding legacy values, the comparable ticket-level total is **₹4,817,881 across 1,690 refund-associated tickets**; average refund is approximately ₹2,851 per refund ticket. Refund-associated tickets are 14.57% of the 11,600-ticket dataset. Monthly, reason, and agent totals each reconcile to ₹4,817,881. `GW-OTHER` is the largest recorded reason at ₹2,195,561 across 745 tickets.

The source also has 775 legacy refund rows with raw values summing to 225,306,200; the policy confirms those values are not stored in rupees but does not document the unit or conversion. Therefore the legacy sum cannot be treated as INR, and no conversion is applied. There are 117 comparable refund tickets with no matched order. The rules identify 125 refund/replacement ticket-level overlaps requiring same-order confirmation; they are review leads, not confirmed policy breaches.

Monthly comparable totals rise sharply around September 2025, when the policy says the new helpdesk went live on 14 September. Treat this as a possible source/reporting discontinuity when interpreting trends. Separately, 225 ticket records link to orders with more than one refund-associated ticket and should be reconciled to the payment/refund ledger before calling them duplicate payments.

The policy prohibits both refund and replacement for the same order and requires same-day escalation. Ticket-level overlap is surfaced for confirmation. The email thread notes a spot check where replacement and refund co-occurred, but gives no validated case count. The policy also says Returns Desk processes most refunds by design; agent totals must be interpreted with team, ticket volume, case mix, and tier. No estimate of preventable refunds or savings is supported by this export alone.

## Validation and next steps

Automated unit tests cover input loading, duplicate selection, missing/malformed amounts, monthly and dimension reconciliation, average-refund denominators, and policy/order-value flags (9 passed). No manual ticket sample, AI model, API usage, or cost was used. Finance should validate the exact legacy conversion against authoritative source-system documentation and payment ledger data; then reconcile a stratified ticket sample to ledger transactions. Support Operations should confirm flagged refund-plus-replacement cases against order outcomes and approval records. Finance should approve any preventability definition or savings target before it is reported.
