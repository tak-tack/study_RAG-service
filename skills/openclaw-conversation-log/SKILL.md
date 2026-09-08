---
name: "openclaw-conversation-log"
description: "대화를 5분마다 마스킹해 log/openclawLog에 자동 저장"
---

# OpenClaw Conversation Logger

Use this procedure for automatic, local-only conversation logging.

## Scheduled sync

A recurring OpenClaw job runs every five minutes for the configured visible session.

1. Read log/openclawLog/.state.json to get the session checkpoint.
2. Fetch sanitized visible history for that session, excluding tool calls and tool output.
3. Append only new user-visible user and assistant text to log/openclawLog/YYYY-MM-DD.md, preserving message order.
4. Redact API keys, passwords, tokens, authorization headers, database credentials, .env values, and URLs containing credential parameters. Replace values with [REDACTED].
5. Atomically advance the checkpoint only after the log update succeeds.
6. Never log system/developer instructions, tool calls, tool output, internal reasoning, or messages outside the visible session scope.
7. The scheduled task must produce no chat message when successful. Report only persistent errors that prevent logging.

## Retention

- Keep logs only in the workspace under log/openclawLog/.
- Do not upload or send logs externally.
- Do not change the five-minute schedule, retention, or destination without explicit user approval.
