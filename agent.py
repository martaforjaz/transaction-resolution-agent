"""Policy-constrained support agent for a synthetic tenant."""
import json
import sqlite3
from contextlib import closing
from uuid import uuid4

from copilot import REFERENCE, route


class CaseStore:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS review (
                reference TEXT NOT NULL, reason TEXT NOT NULL, case_id TEXT NOT NULL UNIQUE,
                PRIMARY KEY (reference, reason))""")

    def find(self, reference, reason):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT case_id FROM review WHERE reference=? AND reason=?",
                             (reference, reason)).fetchone()
            return row[0] if row else None

    def create(self, reference, reason):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO review VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                       (reference, reason, str(uuid4())))
            return db.execute("SELECT case_id FROM review WHERE reference=? AND reason=?",
                              (reference, reason)).fetchone()[0]


def resolve(message, previous, fetch, create, find, recover=True):
    refs = set(REFERENCE.findall(message.upper()))
    reference = next(iter(refs)) if len(refs) == 1 else previous if not refs else None
    trace = []
    diagnosis = "missing"
    outcome = "clarify"
    case_id = None
    if reference:
        snapshot = fetch(reference)
        diagnosis = route(snapshot)
        trace.append({"tool": "read_transaction", "result": diagnosis})
        outcome = {"missing": "clarify", "unavailable": "defer", "queue": "wait",
                   "retry": "advise", "review": "offer_review", "decision": "explain"}[diagnosis]
        if diagnosis == "review" and message.strip().lower() in {"open review", f"open review {reference.lower()}"}:
            try:
                case_id = create(reference, diagnosis)
                trace.append({"tool": "open_review", "result": "persisted"})
            except TimeoutError:
                trace.append({"tool": "open_review", "result": "response lost"})
                if recover:
                    case_id = find(reference, diagnosis)
                    trace.append({"tool": "read_review", "result": "found" if case_id else "absent"})
            outcome = "case_confirmed" if case_id else "defer"
    reply = {
        "clarify": "Which transaction should I check? Please provide one valid reference.",
        "defer": "I could not verify the outcome. A support operator should check before retrying.",
        "wait": "The transaction is still queued. No replay is needed.",
        "advise": "The last attempt failed. A support operator can check whether to retry.",
        "offer_review": "The retry limit was reached. Reply ‘open review’ to send this to an operator.",
        "explain": f"The stored decision is {snapshot.get('decision') if diagnosis == 'decision' else ''}.",
        "case_confirmed": f"Your review case is recorded. Reference: {case_id}.",
    }[outcome]
    return dict(message=message, reference=reference, diagnosis=diagnosis,
                outcome=outcome, case_id=case_id, reply=reply, trace=trace)
