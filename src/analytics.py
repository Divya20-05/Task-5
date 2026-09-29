import pandas as pd

def normalize_date_range(selection, default_start=None, default_end=None):
    """Convert Streamlit's scalar, empty, one-item, or two-item date input to bounds.

    A one-item tuple is the in-progress state after the user selects only the
    range start. Keep the default range end in that state.
    """
    if isinstance(selection, (tuple, list)):
        if len(selection) >= 2:
            return selection[0], selection[1]
        if len(selection) == 1:
            return selection[0], default_end
        return default_start, default_end
    if selection is None:
        return default_start, default_end
    return selection, selection

def filtered(df: pd.DataFrame, start=None, end=None, agent=None, reason=None, product=None) -> pd.DataFrame:
    x=df.copy()
    if start is not None: x=x[x.created_at.dt.date >= start]
    if end is not None: x=x[x.created_at.dt.date <= end]
    if agent: x=x[x.agent_name.astype(str).eq(agent)]
    if reason: x=x[x.refund_reason_code.astype(str).eq(reason)]
    if product: x=x[x.product_product_name.astype(str).eq(product)]
    return x

def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    x=df[df.refund_inr.notna()].groupby("month",dropna=False).agg(refund_total_inr=("refund_inr","sum"),refund_ticket_count=("ticket_id","nunique")).reset_index()
    # The source is ticket-level, so average is total eligible INR / unique eligible
    # refund tickets. Derive it from the same fields shown in the table to keep the
    # denominator explicit and consistent with refund_ticket_count.
    x["average_refund_inr"] = x["refund_total_inr"].div(x["refund_ticket_count"].where(x["refund_ticket_count"].ne(0)))
    x["mom_change_inr"] = x.refund_total_inr.diff()
    x["mom_change_pct"] = x.refund_total_inr.pct_change().where(x.refund_total_inr.shift().ne(0)) * 100
    return x

def dimension_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    x=df[df.refund_inr.notna()].copy()
    result=x.groupby(dimension,dropna=False).agg(refund_total_inr=("refund_inr","sum"),refund_ticket_count=("ticket_id","nunique")).reset_index()
    result["average_refund_inr"] = result["refund_total_inr"].div(result["refund_ticket_count"].where(result["refund_ticket_count"].ne(0)))
    return result.sort_values("refund_total_inr",ascending=False)

def reconciliation(df: pd.DataFrame) -> dict:
    x=df[df.refund_inr.notna()]
    total=float(x.refund_inr.sum())
    return {"eligible_total":total,"monthly_total":float(monthly_summary(df).refund_total_inr.sum()),"reason_total":float(dimension_summary(df,"refund_reason_code").refund_total_inr.sum()),"agent_total":float(dimension_summary(df,"agent_name").refund_total_inr.sum()),"refund_ticket_count":int(x.ticket_id.nunique()),"ticket_denominator":int(df.ticket_id.nunique()),"refund_rate":float(x.ticket_id.nunique()/df.ticket_id.nunique()) if len(df) else None}
