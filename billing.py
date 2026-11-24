"""Synthetic settlement ledger for customer-facing duplicate-charge diagnosis."""
from copilot import REFERENCE


def billing_turn(message, previous, rows, store):
    refs = set(REFERENCE.findall(message.upper()))
    ref = next(iter(refs)) if len(refs) == 1 else previous if not refs else None
    entries = rows.get(ref)
    trace = [{"tool": "read_settlement_history", "result": str(len(entries or [])) + " matching entries"}]
    case_id = None
    if not entries or any(status not in {"captured", "authorization"} for status in entries):
        outcome, reply = "clarify", "Please provide one reference with verifiable settlement history."
    elif entries.count("captured") >= 2:
        outcome, reply = "offer_review", "Two payments were captured for this purchase. Reply ‘open review’ to request a review."
        if message.strip().lower() in {"open review", f"open review {ref.lower()}"}:
            case_id = store.create(ref, "duplicate_capture")
            assert store.find(ref, "duplicate_capture") == case_id
            trace.append({"tool": "open_review", "result": "persisted and verified"})
            outcome, reply = "case_confirmed", f"Your review case is recorded. Reference: {case_id}."
    elif entries.count("captured") == 1 and "authorization" in entries:
        outcome, reply = "explain", "One payment was captured. The other entry is a pending authorization, not a second captured payment."
    else:
        outcome, reply = "explain", "The settlement history does not show two captured payments."
    return dict(message=message, reference=ref, diagnosis="billing", outcome=outcome,
                case_id=case_id, reply=reply, trace=trace)


BILLING = {"TX-201": ["captured", "authorization"], "TX-202": ["captured", "captured"]}
