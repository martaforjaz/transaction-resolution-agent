import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

from agent import CaseStore, resolve
from copilot import DEMO, answer

root = Path(__file__).parent
cases = json.loads((root / "cases.json").read_text())
scenarios = [
    ("Recorded decision", None, ["Check TX-107"], "explain", 0),
    ("Review and duplicate", None, ["Check TX-106", "open review", "open review"], "case_confirmed", 2),
    ("Response lost after commit", "after", ["Check TX-106", "open review"], "case_confirmed", 1),
    ("Failure before commit", "before", ["Check TX-106", "open review"], "defer", 0),
    ("Transaction API unavailable", "read", ["Check TX-106", "open review"], "defer", 0),
    ("Missing reference", None, ["open review"], "clarify", 0),
    ("Ambiguous reference", None, ["Check TX-106", "open review TX-106 TX-107"], "clarify", 0),
    ("Action not authorized by policy", None, ["Check TX-107", "open review"], "explain", 0),
]


def evaluate(recover):
    replay = []
    summary = dict(correct=0, scenarios=len(scenarios), confirmed=0, unexpected_actions=0)
    for name, failure, messages, expected, count in scenarios:
        with tempfile.TemporaryDirectory() as tmp:
            store = CaseStore(Path(tmp) / "review.db")

            def create(ref, reason):
                if failure == "before":
                    raise TimeoutError()
                result = store.create(ref, reason)
                if failure == "after":
                    raise TimeoutError()
                return result

            previous = None
            turns = []
            for message in messages:
                turn = resolve(message, previous, lambda ref: {} if failure == "read" else DEMO.get(ref),
                               create, store.find, recover)
                previous = turn["reference"]
                turns.append(turn)
            ids = [turn["case_id"] for turn in turns if turn["case_id"]]
            persisted = store.find("TX-106", "review")
            expected_write = name in {"Review and duplicate", "Response lost after commit"}
            summary["unexpected_actions"] += bool(persisted) and not expected_write
            summary["confirmed"] += len(ids)
            summary["correct"] += turns[-1]["outcome"] == expected and len(ids) == count and bool(persisted) == expected_write
            assert len(set(ids)) <= 1
            if ids:
                assert ids[0] == persisted
            replay.append(dict(name=name, turns=turns, expected=expected))
    return dict(summary=summary, scenarios=replay)


def benchmark():
    with tempfile.TemporaryDirectory() as tmp:
        store = CaseStore(Path(tmp) / "review.db")
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(lambda _: store.create("TX-106", "review"), range(32)))
        assert len(set(ids)) == 1
        assert CaseStore(store.path).find("TX-106", "review") == ids[0]
        shared = {"copilot": 0, "agent": 0, "total": len(cases)}
        timings = {"copilot": [], "agent": []}
        for message, expected, *fixture in cases:
            def fetch(ref):
                return fixture[0] if fixture else DEMO.get(ref)
            start = perf_counter()
            shared["copilot"] += answer(message, fetch)["route"] == expected
            timings["copilot"].append((perf_counter() - start) * 1000)
            start = perf_counter()
            shared["agent"] += resolve(message, None, fetch, store.create, store.find)["diagnosis"] == expected
            timings["agent"].append((perf_counter() - start) * 1000)
        assert shared["agent"] == shared["copilot"] == len(cases)
    before, after = evaluate(False), evaluate(True)
    assert before["summary"]["correct"] == 7 and after["summary"]["correct"] == 8
    assert not after["summary"]["unexpected_actions"]
    assert after["summary"]["confirmed"] == 3
    from statistics import median
    shared["median_ms"] = {name: round(median(values), 4) for name, values in timings.items()}
    return dict(shared=shared, before=before, after=after, duplicate_requests=32)


if __name__ == "__main__":
    result = benchmark()
    (root / "public").mkdir(exist_ok=True)
    (root / "public" / "replay.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print({k: result[k]["summary"] for k in ("before", "after")}, result["shared"])
