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

![Before reconciliation 7 of 8; after reconciliation 8 of 8](figures/evaluation.svg)

The Copilot and the agent classified the same 20 reference cases correctly. Both share the transaction-state policy, so this check measures parity. Eight additional scripted scenarios cover multi-turn requests, ambiguous references, missing data, unavailable transaction data and write failures. The fixed version passed 8/8, with zero unexpected writes in that suite. A separate test submitted 32 concurrent duplicate case writes and checked that every caller received the same persisted ID, including after reopening the database. Raw turn traces and local diagnostic timings are in [replay.json](public/replay.json).

### Before and after

Select **Response lost after commit** in the replay and advance to the second turn. Before reconciliation, the review existed but the agent could only report an unverified outcome. The corrected version checks the durable record and confirms the existing case ID. If the failure occurred before the write and the record is absent, it defers to a support operator. GitHub Actions runs the same regression suite and builds the UI.

The reference agent uses fixed policies and response templates. The synthetic environment is single-tenant, and the local endpoints assume a trusted operator. Review records demonstrate a handoff queue in the database.

With the Java stack running, run python verify_live.py to check a real asynchronous decision after equivalent submissions to both feeds.
