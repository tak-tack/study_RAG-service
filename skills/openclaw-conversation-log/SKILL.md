---
name: "openclaw-conversation-log"
description: "대화를 마스킹해 log/openclawLog에 저장"
---

# OpenClaw Conversation Logger

Use this procedure when the user asks to retain their conversation history.

1. List only sessions visible to the current user and agent scope.
2. Fetch the target session history with tool calls excluded.
3. Redact sensitive values before writing:
   - API keys, passwords, tokens, authorization headers, database credentials, private URLs with embedded credentials, and values from .env files.
   - Replace each with `[REDACTED]`; preserve surrounding explanation when safe.
4. Append the sanitized transcript to `log/openclawLog/YYYY-MM-DD.md`.
   - Add a session heading with the session ID and export time.
   - Preserve message order and role labels.
   - Do not duplicate messages already recorded for that session; record the last exported message identifier or timestamp in a sidecar state file under the same folder.
5. Never write tool output or internal system/developer instructions into the user-facing log.
6. If session visibility does not include older conversations, state that limitation rather than claiming a complete archive.

## Retention

- Keep logs local to the workspace.
- Do not upload or send the logs externally.
- Before changing retention or enabling scheduled execution, request explicit user approval.
