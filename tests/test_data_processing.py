import pandas as pd
from src.data_loader import load_inputs
from src.data_processing import prepare_data

def test_actual_inputs_load_and_required_fields():
    raw=load_inputs()
    assert {"ticket_id","created_at","refund_amount_inr"}.issubset(raw["tickets"].columns)
    assert len(raw["tickets"])>0

def test_duplicate_prefers_helpdesk_and_legacy_excluded():
    tickets=pd.DataFrame([
        {"ticket_id":"T1","created_at":"2025-01-01","agent_id":"A","customer_id":"C","order_id":"O","product_sku":"P","refund_amount_inr":1000,"source_system":"legacy_fd"},
        {"ticket_id":"T1","created_at":"2025-01-01","agent_id":"A","customer_id":"C","order_id":"O","product_sku":"P","refund_amount_inr":10,"source_system":"helpdesk"},
    ])
    raw={"tickets":tickets,"agents":pd.DataFrame([{"agent_id":"A","name":"Agent"}]),"orders":pd.DataFrame(),"customers":pd.DataFrame(),"products":pd.DataFrame()}
    out=prepare_data(raw)
    assert len(out)==1 and out.iloc[0].refund_inr==10
    assert bool(out.iloc[0].duplicate_ticket_id)

def test_invalid_amount_is_not_zero():
    t=pd.DataFrame([{"ticket_id":"T","created_at":"bad","agent_id":"A","refund_amount_inr":"oops","source_system":"helpdesk"}])
    raw={"tickets":t,"agents":pd.DataFrame(),"orders":pd.DataFrame(),"customers":pd.DataFrame(),"products":pd.DataFrame()}
    out=prepare_data(raw)
    assert pd.isna(out.iloc[0].refund_inr)
