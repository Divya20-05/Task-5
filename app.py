from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_inputs
from src.data_processing import prepare_data, data_quality
from src.analytics import filtered, monthly_summary, dimension_summary, reconciliation, normalize_date_range
from src.anomaly_detection import flag_cases

st.set_page_config(page_title="Vireo Refund Intelligence", page_icon="🔎", layout="wide")
st.title("Vireo Audio · Refund Intelligence")
st.caption("Deterministic finance analysis with traceable records. Flags invite review; they do not determine fault.")

@st.cache_data(show_spinner="Loading source files…")
def get_data():
    raw=load_inputs(Path(__file__).resolve().parent)
    return raw, prepare_data(raw)

try:
    raw, all_tickets=get_data()
except Exception as exc:
    st.error(f"Could not load project data: {exc}"); st.stop()

min_date=all_tickets.created_at.min(); max_date=all_tickets.created_at.max()
with st.sidebar:
    st.header("Filters")
    if pd.notna(min_date) and pd.notna(max_date):
        dates=st.date_input("Ticket creation date",value=(min_date.date(),max_date.date()),min_value=min_date.date(),max_value=max_date.date())
        start,end=normalize_date_range(dates,min_date.date(),max_date.date())
    else: start=end=None
    agents=[str(v) for v in sorted(all_tickets.agent_name.dropna().unique())]
    reasons=[str(v) for v in sorted(all_tickets.refund_reason_code.dropna().unique())]
    products=[str(v) for v in sorted(all_tickets.product_product_name.dropna().unique())]
    agent=st.selectbox("Resolving agent",["All"]+agents)
    reason=st.selectbox("Refund reason",["All"]+reasons)
    product=st.selectbox("Product",["All"]+products)
    st.caption("All monetary totals include comparable current-helpdesk amounts only (INR). Legacy values are retained for inspection but excluded from financial aggregation.")

df=filtered(all_tickets,start,end,None if agent=="All" else agent,None if reason=="All" else reason,None if product=="All" else product)
df=flag_cases(df)
st.caption(f"Applied period: {start or 'all'} to {end or 'all'} · {len(df):,} unique ticket IDs · filters apply across views")
tabs=st.tabs(["Executive overview","Monthly trends","Reasons","Agents","Review flags","Ticket explorer","Data quality"])

with tabs[0]:
    rec=reconciliation(df); eligible=df[df.refund_inr.notna()]
    k=st.columns(4); k[0].metric("Comparable refunds",f"₹{rec['eligible_total']:,.0f}"); k[1].metric("Refund-associated tickets",f"{rec['refund_ticket_count']:,}"); k[2].metric("Average refund / ticket",f"₹{eligible.refund_inr.mean():,.0f}" if len(eligible) else "—"); k[3].metric("Refund ticket rate",f"{rec['refund_rate']:.1%}" if rec['refund_rate'] is not None else "—")
    st.caption("Refund ticket rate = unique tickets with an eligible INR refund ÷ unique tickets in the filtered population. A ticket is not necessarily a separate payment transaction.")
    m=monthly_summary(df)
    if m.empty: st.info("No comparable INR refunds in this filter.")
    else:
        monthly_chart=px.bar(m,x="month",y="refund_total_inr",title="Monthly comparable refunds (INR)",labels={"month":"Calendar month","refund_total_inr":"Refund amount (₹)"})
        monthly_chart.update_xaxes(type="category")
        monthly_chart.update_yaxes(rangemode="tozero",tickprefix="₹",tickformat=",.0f")
        st.plotly_chart(monthly_chart,use_container_width=True)
        st.caption("Each bar is the total for one calendar month. A date filter contained within one month produces one monthly bar.")
        st.subheader("Largest reason totals")
        reason_totals=dimension_summary(df,"refund_reason_code")
        st.dataframe(reason_totals.style.format({"refund_total_inr":"₹{:,.2f}","refund_ticket_count":"{:,.0f}","average_refund_inr":"₹{:,.2f}"}),use_container_width=True,hide_index=True)
    st.info("Observed refunds are not equivalent to avoidable leakage. The supplied files do not establish preventability or savings; Finance must validate any target.")
with tabs[1]:
    m=monthly_summary(df)
    if m.empty: st.info("No comparable INR refund tickets for the selected filters.")
    else:
        st.plotly_chart(px.bar(m,x="month",y="refund_total_inr",title="Monthly refund amount",labels={"month":"Calendar month","refund_total_inr":"INR"}),use_container_width=True)
        st.dataframe(m,use_container_width=True,hide_index=True)
with tabs[2]:
    r=dimension_summary(df,"refund_reason_code")
    if r.empty: st.info("No comparable refund records.")
    else:
        st.plotly_chart(px.bar(r,x="refund_reason_code",y="refund_total_inr",title="Refund amounts by source reason code",labels={"refund_reason_code":"Original reason code","refund_total_inr":"INR"}),use_container_width=True)
        st.dataframe(r,use_container_width=True,hide_index=True)
        by_month=df[df.refund_inr.notna()].groupby(["month","refund_reason_code"],dropna=False).refund_inr.sum().reset_index(name="refund_total_inr")
        st.plotly_chart(px.line(by_month,x="month",y="refund_total_inr",color="refund_reason_code",markers=True,title="Monthly refund trend by source reason code",labels={"month":"Calendar month","refund_total_inr":"INR","refund_reason_code":"Reason code"}),use_container_width=True)
        st.subheader("Product totals")
        st.dataframe(dimension_summary(df,"product_product_name"),use_container_width=True,hide_index=True)
        st.caption("Reason codes are the agent-selected source values. The policy describes their meanings; this ranking does not assign fault.")
with tabs[3]:
    a=dimension_summary(df,"agent_name")
    if a.empty: st.info("No comparable refund records.")
    else:
        if "agent_team" in df:
            teams=df.groupby("agent_name").agent_team.first(); a["team"]=a.agent_name.map(teams)
        volume=df.groupby("agent_name").ticket_id.nunique().rename("ticket_volume")
        a=a.merge(volume,on="agent_name",how="left")
        a["refund_ticket_rate"] = a.refund_ticket_count / a.ticket_volume
        st.plotly_chart(px.bar(a,x="agent_name",y="refund_total_inr",color="team" if "team" in a else None,title="Refund totals by resolving agent",labels={"agent_name":"Agent","refund_total_inr":"INR","team":"Roster team"}),use_container_width=True)
        st.dataframe(a,use_container_width=True,hide_index=True)
        st.caption("Interpret alongside assigned team, roster changes, ticket volume, case mix, and policy. Returns Desk is expected to process most refunds; Tier 2 and Tier 1 volume should not be compared as equivalent work.")
with tabs[4]:
    flagged=df[df.anomaly_flags.ne("")]
    st.write(f"{len(flagged):,} ticket records carry one or more review/data-quality flags.")
    st.caption("Policy flag: the policy prohibits refund plus replacement for the same order and requires same-day escalation. Ticket-level co-occurrence needs order-level confirmation.")
    st.dataframe(flagged,use_container_width=True,hide_index=True)
    if len(flagged): st.download_button("Download flagged records CSV",flagged.to_csv(index=False).encode("utf-8-sig"),"vireo_flagged_tickets.csv","text/csv")
with tabs[5]:
    query=st.text_input("Search ticket ID, narrative, agent, order")
    view=df
    if query:
        mask=pd.Series(False,index=view.index)
        for c in ["ticket_id","customer_message","agent_notes","agent_name","order_id"]:
            if c in view: mask|=view[c].astype("string").str.contains(query,case=False,na=False)
        view=view[mask]
    cols=[c for c in ["ticket_id","created_at","agent_name","agent_team","refund_reason_code","refund_amount_inr","refund_inr","order_id","order_order_value_inr","product_product_name","replacement_issued","anomaly_flags","customer_message","agent_notes","source_system"] if c in view]
    st.dataframe(view[cols],use_container_width=True,hide_index=True)
    st.download_button("Download filtered ticket CSV",view[cols].to_csv(index=False).encode("utf-8-sig"),"vireo_filtered_tickets.csv","text/csv")
with tabs[6]:
    q=data_quality(raw,all_tickets)
    st.subheader("Source and reconciliation checks")
    st.json(q)
    rec=reconciliation(df)
    st.write("Filtered totals reconciliation",rec)
    st.caption("Monthly, reason, and agent INR subtotals should each equal the eligible total; unknown labels remain represented in the breakdowns. Missing amounts are excluded, never treated as zero.")
    st.dataframe(pd.DataFrame([{"input_file":f,"rows":len(d),"exact_duplicate_rows":int(d.duplicated().sum()),"missing_cells":int(d.isna().sum().sum())} for f,d in raw.items()]),hide_index=True,use_container_width=True)
