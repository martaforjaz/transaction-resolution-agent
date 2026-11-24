# Transaction Resolution Agent

![Conversation, transaction lookup and verified review action](figures/agent.svg)

A support agent for synthetic payment transactions. It reads transaction state from a Spring Boot service backed by Kafka and PostgreSQL. When the retry limit is exhausted, the agent offers to open a review case and waits for an explicit request before writing it. The React and TypeScript interface shows the conversation alongside each tool outcome.

[Open the interactive replay](https://martaforjaz.github.io/transaction-resolution/) · [Transaction service](https://github.com/martaforjaz/transaction-risk-integration-service) · [Original support copilot](https://github.com/martaforjaz/transaction-support-copilot)

## Run locally

Start the linked Java service with its Docker Compose instructions. In this repository, run:

```sh
python evaluate.py
npm ci
npm run build -- --base=./
python server.py
```

Open http://127.0.0.1:8765 and select **Connect to local Java service**. Submit a synthetic payment to the Java gateway, then ask the agent about its UUID. The server defaults to the Java loopback endpoint on port 8080. Set `RISK_SERVICE_URL` to change it. Review cases are stored in a separate local SQLite database with a unique transaction-and-reason key. The public replay serves recorded synthetic fixtures.

## Evaluation

![Before reconciliation 9 of 10; after reconciliation 10 of 10](figures/evaluation.svg)

The Copilot and the agent classified the same 20 reference cases correctly. Both share the transaction-state policy, so this check measures parity. Ten additional scripted scenarios cover multi-turn requests, ambiguous references, missing data, unavailable transaction data and write failures. The fixed version passed 10/10, with zero unexpected writes in that suite. A separate test submitted 32 concurrent duplicate case writes and checked that every caller received the same persisted ID, including after reopening the database. Raw turn traces and local diagnostic timings are in [replay.json](public/replay.json).

### Before and after

Select **Response lost after commit** in the replay and advance to the second turn. Before reconciliation, the review existed but the agent could only report an unverified outcome. The corrected version checks the durable record and confirms the existing case ID. If the failure occurred before the write and the record is absent, it defers to a support operator. GitHub Actions runs the same regression suite and builds the UI.

The reference agent uses fixed policies and response templates. The synthetic environment is single-tenant, and the local endpoints assume a trusted operator. Review records demonstrate a handoff queue in the database.

With the Java stack running, run python verify_live.py to check a real asynchronous decision after equivalent submissions to both feeds.

## Duplicate-charge investigation

Try TX-201 and TX-202 in the local conversation or choose their recorded scenarios. A separate synthetic settlement ledger supplies authorization and capture status. The Java risk decision measures a different stage in the payment lifecycle. On a confirmed double capture, an explicit review request creates and verifies a durable case.

The replay data records median and maximum end-to-end **local scenario execution** times, from the first turn through the last tool result, including SQLite writes when applicable. These measurements exclude human response time and external network latency.

## Device Troubleshooting Agent

[Launch the browser simulator](https://martaforjaz.github.io/transaction-resolution/?router). Compare local DNS failure, a provider outage and a healthy router. The diagnosis checks WAN and DNS telemetry. A restart requires consent, repeated consent cannot dispatch a second restart within the same scenario, and a subsequent connectivity probe either verifies recovery or escalates the case. The UI counts required customer steps. Run `node router.test.mjs` with Node 24 to reproduce the state-machine checks. All router telemetry and actions are simulated.
