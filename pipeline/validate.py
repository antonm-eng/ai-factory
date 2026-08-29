"""Step 2: validate the extracted batch against its data contract."""

import sqlite3

from pipeline.contracts import load_contract


class ContractViolation(Exception):
    pass


def validate(conn: sqlite3.Connection) -> dict:
    contract = load_contract("recharge_events")
    actual = [r[1] for r in conn.execute("PRAGMA table_info(recharge_events)")]
    expected = [c["name"] for c in contract["columns"]]
    if actual != expected:
        raise ContractViolation(f"recharge_events columns {actual} do not match contract {expected}")

    total = conn.execute("SELECT COUNT(*) FROM recharge_events").fetchone()[0]
    if total == 0:
        raise ContractViolation("recharge_events batch is empty")

    for col in contract["columns"]:
        if col.get("allowed"):
            placeholders = ", ".join("?" for _ in col["allowed"])
            bad = conn.execute(
                f"SELECT COUNT(*) FROM recharge_events WHERE {col['name']} NOT IN ({placeholders})", col["allowed"]
            ).fetchone()[0]
            if bad:
                raise ContractViolation(f"{bad} rows have unexpected values in {col['name']}")

    return {"rows": total, "contract_version": contract["contract_version"]}
