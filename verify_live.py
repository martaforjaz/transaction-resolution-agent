"""Verify the local HTTP agent against a running Java/Kafka/PostgreSQL stack."""
import json
import os
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

from agent import CaseStore
import server

BASE = os.getenv("RISK_SERVICE_URL", "http://127.0.0.1:8080")


def post(url, data):
    req = Request(url, json.dumps(data).encode(), {"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as res:
        return json.load(res)


def main():
    reference = str(uuid4())
    first = post(BASE + "/transactions/gateway", dict(id=reference, amountMinor=1250, currency="EUR"))
    post(BASE + "/transactions/ledger", dict(reference=reference, total="12.50", ccy="EUR"))
    os.environ["RISK_SERVICE_URL"] = BASE
    from threading import Thread

    with tempfile.TemporaryDirectory() as folder:
        server.store = CaseStore(Path(folder) / "cases.sqlite")
        with server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler) as gateway:
            worker = Thread(target=gateway.serve_forever, daemon=True)
            worker.start()
            try:
                url = f"http://127.0.0.1:{gateway.server_port}/api/turn"
                for _ in range(40):
                    turn = post(url, dict(message=f"Check {reference}"))
                    if turn["outcome"] == "explain":
                        break
                    time.sleep(.5)
                assert turn["outcome"] == "explain", turn
                followup = post(url, dict(message="open review", previous=reference))
                assert followup["case_id"] is None and followup["outcome"] == "explain"
                assert first["id"] == reference
                with urlopen(f"{BASE}/transactions/{reference}", timeout=5) as res:
                    state = json.load(res)
                assert state["attempts"] == 1 and state["decision"] in turn["reply"]
                assert server.store.find(reference.upper(), "review") is None
                authorization = post(url, dict(message="I think I was charged twice for TX-201"))
                assert authorization["outcome"] == "explain" and "pending authorization" in authorization["reply"]
                captured = post(url, dict(message="Check TX-202"))
                assert captured["outcome"] == "offer_review"
                assert server.store.find("TX-202", "duplicate_capture") is None
                first_case = post(url, dict(message="open review", previous="tx-202"))
                repeated = post(url, dict(message="open review", previous="TX-202"))
                assert first_case["case_id"] and repeated["case_id"] == first_case["case_id"]
                print("Verified Java decisions, duplicate feed submissions and both billing flows through HTTP.")
            finally:
                gateway.shutdown()
                worker.join()


if __name__ == "__main__":
    main()
