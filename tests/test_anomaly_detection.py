import pandas as pd
from src.anomaly_detection import flag_cases

def test_policy_and_over_order_value_flags():
    d=pd.DataFrame([{"ticket_id":"T","refund_inr":1200,"replacement_issued":"Y","order_order_value_inr":1000,"duplicate_ticket_id":False,"source_system":"helpdesk","agent_id":"A","refund_reason_code":"DOA-REPL"}])
    f=flag_cases(d).iloc[0].anomaly_flags
    assert "refund and replacement" in f.lower()
    assert "exceeds matched order value" in f.lower()

def test_repeated_refunds_for_one_order_are_review_flags():
    d=pd.DataFrame([{"ticket_id":"T1","order_id":"O1","refund_inr":100,"replacement_issued":"N"},{"ticket_id":"T2","order_id":"O1","refund_inr":200,"replacement_issued":"N"}])
    flagged=flag_cases(d)
    assert flagged.anomaly_flags.str.contains("More than one refund-associated ticket",regex=False).all()
