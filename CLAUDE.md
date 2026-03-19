# DevMind — AI-Powered Personal Dev Assistant

## Project Overview
A multi-agent developer assistant powered by the OpenAI Agents SDK.
Reads your local files, searches GitHub, and browses the web to answer dev questions.

## Architecture
- **4 agents**: Triage → Code Review | Repo Search | Web Research
- **3 MCP servers**: Filesystem, GitHub, Brave Search (via npx — no tool code needed)
- **Guardrails**: input (empty, jailbreak, path traversal) + output (PII, length)
- **Memory**: SQLiteSession persists conversation history across turns

## Project Structure
```
src/devmind/
├── main.py                  # CLI entry point
├── config.py                # Env vars + constants
├── agents/
│   ├── triage_agent.py      # Routes to specialists (GPT-4o-mini)
│   ├── code_review_agent.py # Code review via Filesystem + GitHub MCP
│   ├── repo_search_agent.py # Repo search via GitHub + Filesystem MCP
│   └── web_research_agent.py# Web research via Brave + Filesystem MCP
├── guardrails/
│   ├── input_guards.py      # empty, jailbreak, path_traversal guards
│   └── output_guards.py     # pii, length guards
├── mcp/
│   └── servers.py           # MCPServerStdio factory functions
└── session/
    └── memory.py            # SQLiteSession factory
```

## MCP Servers Used
All three MCP servers are installed **on demand via npx** — no npm install needed:
- `@modelcontextprotocol/server-filesystem` — read/write local files
- `@modelcontextprotocol/server-github` — search GitHub repos and code
- `@modelcontextprotocol/server-brave-search` — real web search

## Running
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in keys
python -m src.devmind.main
```

## Key SDK Concepts Demonstrated
- `MCPServerStdio` — connect agents to external MCP servers
- Multi-MCP — one agent using 2 MCP servers simultaneously
- `handoff()` with `input_type` — structured handoff metadata
- `SQLiteSession` — persistent cross-turn memory
- `@input_guardrail` / `@output_guardrail` — tripwire pattern

## Environment Variables
| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI key |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Yes | GitHub PAT (repo + read:org scopes) |
| `BRAVE_API_KEY` | Yes | Brave Search API key |
| `FS_ROOT_PATH` | Yes | Filesystem root for MCP (e.g. /Users/yourname) |
| `SESSION_ID` | No | Conversation ID (default: devmind-user) |
| `DB_PATH` | No | SQLite path (default: data/conversations.db) |
