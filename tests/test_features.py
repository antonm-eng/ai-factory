import sqlite3
import unittest
from datetime import datetime

from pipeline.features import build_features

RUN_TS = datetime(2026, 10, 7, 2, 0, 0)

FIXTURE = [
    ("rc_1", "sub_a", "2026-10-01 10:00:00", 5.0, "digital", "prepaid"),
    ("rc_2", "sub_a", "2026-10-05 09:30:00", 10.0, "retail", "prepaid"),
    ("rc_3", "sub_b", "2026-09-20 18:15:00", 3.0, "ussd", "prepaid"),
]


class BuildFeaturesTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE recharge_events (event_id TEXT, msisdn_hash TEXT, recharge_ts TEXT, "
            "amount_azn REAL, channel TEXT, plan_type TEXT)"
        )
        self.conn.executemany("INSERT INTO recharge_events VALUES (?, ?, ?, ?, ?, ?)", FIXTURE)

    def test_recharge_features(self):
        counts = build_features(self.conn, RUN_TS)
        self.assertEqual(counts, {"recharge": 2, "usage": 2})
        row = self.conn.execute(
            "SELECT recharge_cnt_30d, avg_recharge_30d, digital_share_30d FROM features_recharge WHERE msisdn_hash = 'sub_a'"
        ).fetchone()
        self.assertEqual(row, (2, 7.5, 0.5))


if __name__ == "__main__":
    unittest.main()
