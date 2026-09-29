from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FILES = {"tickets": "tickets.csv", "agents": "agents.csv", "orders": "orders.csv", "customers": "customers.csv", "products": "products.csv"}
REQUIRED = {"tickets": {"ticket_id", "created_at", "agent_id", "refund_amount_inr"}, "agents": {"agent_id"}}

def load_inputs(root: Path = ROOT) -> dict[str, pd.DataFrame]:
    data = {}
    for name, filename in FILES.items():
        path = root / filename
        if not path.exists():
            if name in REQUIRED:
                raise FileNotFoundError(f"Required input file is missing: {path}")
            data[name] = pd.DataFrame()
            continue
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", dtype={"ticket_id":"string", "agent_id":"string", "order_id":"string", "customer_id":"string", "product_sku":"string", "sku":"string"})
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            try:
                df = pd.read_csv(path, encoding="cp1252", dtype="string")
            except Exception as retry:
                raise ValueError(f"Could not read {filename}: {retry}") from exc
        missing = REQUIRED.get(name, set()) - set(df.columns)
        if missing:
            raise ValueError(f"{filename} is missing required columns: {', '.join(sorted(missing))}")
        data[name] = df
    return data
