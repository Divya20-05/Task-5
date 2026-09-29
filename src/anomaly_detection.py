import pandas as pd

def flag_cases(df: pd.DataFrame) -> pd.DataFrame:
    x=df.copy(); flags=[]; classes=[]
    repeated_orders=set()
    if "order_id" in x:
        order_counts=x.loc[x.refund_inr.notna() & x.order_id.notna()].groupby("order_id").ticket_id.nunique()
        repeated_orders=set(order_counts[order_counts.gt(1)].index.astype(str))
    for _,r in x.iterrows():
        f=[]; c=[]
        if pd.notna(r.get("refund_inr")) and str(r.get("replacement_issued","N")).strip().upper()=="Y":
            f.append("Refund and replacement on ticket; policy says not both for the same order. Verify order-level outcome."); c.append("Policy review")
        if pd.notna(r.get("refund_inr")) and pd.notna(r.get("order_order_value_inr")) and r.refund_inr > r.order_order_value_inr:
            f.append(f"Refund ₹{r.refund_inr:,.2f} exceeds matched order value ₹{r.order_order_value_inr:,.2f}."); c.append("Review")
        if pd.notna(r.get("refund_inr")) and pd.notna(r.get("order_id")) and str(r.order_id) in repeated_orders:
            f.append("More than one refund-associated ticket references this order; reconcile against payment/refund ledger."); c.append("Review")
        if bool(r.get("duplicate_ticket_id",False)):
            f.append("Ticket ID appeared in multiple source rows; current-system row was selected where available."); c.append("Data quality")
        if pd.notna(r.get("refund_inr")) and (str(r.get("refund_reason_code","Unknown")) in ("Unknown","<NA>","")):
            f.append("Comparable refund has no reason code."); c.append("Data quality")
        if pd.notna(r.get("refund_amount_inr")) and pd.isna(r.get("refund_inr")) and str(r.get("source_system"))=="legacy_fd":
            f.append("Legacy refund amount excluded from INR totals: source policy says legacy native unit differs, conversion is undocumented."); c.append("Data quality")
        if pd.notna(r.get("refund_inr")) and pd.isna(r.get("agent_id")):
            f.append("Refund ticket has no agent reference."); c.append("Data quality")
        if pd.notna(r.get("refund_amount_raw")) and pd.isna(pd.to_numeric(pd.Series([r.get("refund_amount_raw")]), errors="coerce").iloc[0]):
            f.append("Refund amount is malformed and excluded from financial totals."); c.append("Data quality")
        if pd.notna(r.get("refund_amount_inr")) and pd.to_numeric(r.get("refund_amount_inr"), errors="coerce") < 0:
            f.append("Refund amount is negative; verify source adjustment or reversal semantics."); c.append("Data quality")
        flags.append("; ".join(f)); classes.append("; ".join(sorted(set(c))))
    x["anomaly_flags"]=flags; x["review_class"]=classes
    return x
