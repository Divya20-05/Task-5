import pandas as pd
from src.analytics import monthly_summary,dimension_summary,reconciliation,filtered,normalize_date_range
from src.data_loader import load_inputs
from src.data_processing import prepare_data

def fixture():
    return pd.DataFrame({"ticket_id":["1","2","3"],"month":["2025-01","2025-01","2025-02"],"refund_inr":[100.,200.,None],"refund_reason_code":["A","B","A"],"agent_name":["X","Y","X"]})

def test_monthly_and_breakdown_reconcile():
    d=fixture(); m=monthly_summary(d)
    assert m.refund_total_inr.sum()==300
    assert dimension_summary(d,"refund_reason_code").refund_total_inr.sum()==300
    assert reconciliation(d)["eligible_total"]==300

def test_refund_rate_denominator_is_all_filtered_tickets():
    assert reconciliation(fixture())["refund_rate"]==2/3

def test_dimension_average_uses_displayed_unique_refund_ticket_denominator():
    d=pd.DataFrame({"ticket_id":["1","2","3","4"],"month":["2025-01"]*4,"refund_inr":[100.,200.,300.,None],"refund_reason_code":["A","A","A","A"],"agent_name":["X","X","Y","Y"]})
    summary=dimension_summary(d,"refund_reason_code").iloc[0]
    assert summary.refund_total_inr==600
    assert summary.refund_ticket_count==3
    assert summary.average_refund_inr==200

def test_actual_source_month_reason_agent_totals_and_averages_reconcile():
    tickets=prepare_data(load_inputs())
    eligible=tickets[tickets.refund_inr.notna()]
    expected_total=eligible.refund_inr.sum()
    for summary, dimension in ((monthly_summary(tickets),"month"),(dimension_summary(tickets,"refund_reason_code"),"refund_reason_code"),(dimension_summary(tickets,"agent_name"),"agent_name")):
        assert summary.refund_total_inr.sum()==expected_total
        assert summary.refund_ticket_count.sum()==eligible.ticket_id.nunique()
        expected_average=summary.refund_total_inr.div(summary.refund_ticket_count)
        assert (summary.average_refund_inr.sub(expected_average).abs()<1e-10).all()

def test_date_range_normalizes_in_progress_single_start_and_filters_records():
    from datetime import date
    minimum=date(2025,1,1); maximum=date(2025,1,5); selected=date(2025,1,3)
    start,end=normalize_date_range((selected,),minimum,maximum)
    assert (start,end)==(selected,maximum)
    d=pd.DataFrame({"ticket_id":["1","2","3"],"created_at":pd.to_datetime(["2025-01-02","2025-01-03","2025-01-04"]),"agent_name":["A"]*3,"refund_reason_code":["A"]*3,"product_product_name":["P"]*3})
    out=filtered(d,start,end)
    assert out.ticket_id.tolist()==["2","3"]

def test_date_range_normalizes_two_item_empty_and_scalar_values():
    from datetime import date
    lo=date(2025,1,2); hi=date(2025,1,4); default_lo=date(2025,1,1); default_hi=date(2025,1,5)
    assert normalize_date_range((lo,hi),default_lo,default_hi)==(lo,hi)
    assert normalize_date_range((),default_lo,default_hi)==(default_lo,default_hi)
    assert normalize_date_range(lo,default_lo,default_hi)==(lo,lo)
