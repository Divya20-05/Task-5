import pandas as pd

def _clean_text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

def prepare_data(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One investigation row per ticket; helpdesk representation wins over its legacy import."""
    t = raw["tickets"].copy()
    for col in ("ticket_id", "agent_id", "customer_id", "order_id", "product_sku", "refund_reason_code", "source_system", "replacement_issued"):
        if col in t: t[col] = _clean_text(t[col])
    t["created_at"] = pd.to_datetime(t.get("created_at"), errors="coerce")
    for col in ("resolved_at", "first_response_at"):
        if col in t: t[col] = pd.to_datetime(t[col], errors="coerce")
    t["refund_amount_raw"] = t["refund_amount_inr"]
    t["refund_amount_inr"] = pd.to_numeric(t["refund_amount_inr"], errors="coerce")
    t["source_system"] = t.get("source_system", pd.Series("unknown", index=t.index)).fillna("unknown").str.lower()
    t["has_refund_amount"] = t["refund_amount_inr"].notna()
    t["is_inr_comparable"] = t["has_refund_amount"] & t["source_system"].eq("helpdesk")
    t["refund_inr"] = t["refund_amount_inr"].where(t["is_inr_comparable"])
    t["duplicate_ticket_id"] = t.duplicated("ticket_id", keep=False)
    # Duplicate migration exports retain source rows in raw inputs. Prefer current-system
    # row for ticket-level analytics; where absent, retain legacy row for investigation.
    t["_source_rank"] = t["source_system"].map({"helpdesk": 0, "legacy_fd": 1}).fillna(2)
    t = t.sort_values(["_source_rank"]).drop_duplicates("ticket_id", keep="first").drop(columns="_source_rank")
    for name, key, right_key in (("agents","agent_id","agent_id"),("orders","order_id","order_id"),("customers","customer_id","customer_id"),("products","product_sku","sku")):
        dim = raw.get(name, pd.DataFrame())
        if dim.empty or key not in t or right_key not in dim: continue
        dim = dim.copy()
        if dim[right_key].duplicated().any():
            dim = dim.drop_duplicates(right_key, keep="first")
        rename = {c: f"{name[:-1]}_{c}" for c in dim.columns if c != right_key}
        t = t.merge(dim.rename(columns=rename), left_on=key, right_on=right_key, how="left", validate="many_to_one")
        if right_key != key and right_key in t: t = t.drop(columns=[right_key])
    # Fallback order linkage only when exactly one order matches customer and SKU.
    if "order_order_value_inr" in t:
        missing_order = t["order_id"].isna()
        orders = raw.get("orders", pd.DataFrame())
        if not orders.empty and {"customer_id","sku","order_id"}.issubset(orders.columns):
            counts = orders.groupby(["customer_id","sku"])["order_id"].nunique()
            unique_pairs = counts[counts.eq(1)].index
            lookup = orders.drop_duplicates(["customer_id","sku"]).set_index(["customer_id","sku"])
            for idx in t.index[missing_order]:
                pair = (t.at[idx,"customer_id"], t.at[idx,"product_sku"])
                if pair in unique_pairs:
                    row = lookup.loc[pair]
                    t.at[idx,"order_id"] = row["order_id"]
                    t.at[idx,"order_order_value_inr"] = row["order_value_inr"]
                    if "order_lot_code" in t: t.at[idx,"order_lot_code"] = row.get("lot_code")
    t["month"] = t["created_at"].dt.to_period("M").astype("string")
    t["refund_reason_code"] = t.get("refund_reason_code", pd.Series(index=t.index,dtype="string")).fillna("Unknown")
    t["agent_name"] = t.get("agent_name", t.get("agent_id", pd.Series("Unknown", index=t.index))).fillna(t.get("agent_id", "Unknown"))
    t["product_product_name"] = t.get("product_product_name", t.get("product_sku", pd.Series("Unknown", index=t.index))).fillna(t.get("product_sku", "Unknown"))
    return t

def data_quality(raw: dict[str, pd.DataFrame], prepared: pd.DataFrame) -> dict:
    tickets = raw["tickets"]
    legacy_refunds = tickets["refund_amount_inr"].notna() & tickets.get("source_system", pd.Series(index=tickets.index)).eq("legacy_fd")
    parsed = pd.to_numeric(tickets["refund_amount_inr"], errors="coerce")
    return {"source_ticket_rows":len(tickets),"unique_ticket_ids":tickets["ticket_id"].nunique(),"duplicate_ticket_rows":int(tickets["ticket_id"].duplicated(keep=False).sum()),"legacy_refund_rows_excluded":int(legacy_refunds.sum()),"legacy_refund_raw_sum_unconverted":float(parsed[legacy_refunds].sum()),"missing_amount_rows":int(tickets["refund_amount_inr"].isna().sum()),"invalid_amount_rows":int((tickets["refund_amount_inr"].notna() & parsed.isna()).sum()),"zero_amount_rows":int(parsed.eq(0).sum()),"negative_amount_rows":int(parsed.lt(0).sum()),"eligible_refund_tickets":int(prepared["refund_inr"].notna().sum()),"missing_agent_join":int(prepared.get("agent_name",pd.Series(index=prepared.index)).isna().sum()),"unmatched_order_join":int(prepared.loc[prepared["refund_inr"].notna(),"order_id"].isna().sum()) if "order_id" in prepared else 0,"unmatched_customer_join":int(prepared.loc[prepared["refund_inr"].notna(),"customer_name"].isna().sum()) if "customer_name" in prepared else 0,"unmatched_product_join":int(prepared.loc[prepared["refund_inr"].notna(),"product_product_name"].isna().sum()) if "product_product_name" in prepared else 0,"missing_dates":int(prepared["created_at"].isna().sum())}
