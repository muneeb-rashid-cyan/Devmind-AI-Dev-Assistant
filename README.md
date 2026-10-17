# DevMind — AI-Powered Personal Dev Assistant

> Ask questions like you're talking to a senior developer sitting next to you.
> DevMind reads your actual code, searches all of GitHub, and browses the live web to answer.

Built with **OpenAI Agents SDK** · **MCP Servers** · **Multi-Agent Handoffs** · **SQLite Memory**

---

## What It Does

You type a question. DevMind figures out what you need and routes it to the right specialist agent — which then uses real tools (MCP servers) to fetch actual data before answering.

```
You:      "review src/devmind/guardrails/input_guards.py"

DevMind:  [handoff → Code Review Agent]
          → reads your file via Filesystem MCP
          → searches GitHub for similar guardrail patterns
          → "Line 58: the empty input check uses < 3 chars which
             might be too aggressive for short commands like 'ls'..."
```

---

## Architecture

```
Your Input
    │
    ▼
Triage Agent (GPT-4o-mini)         ← 3 input guardrails
    │
    ├── file / code question   →   Code Review Agent (GPT-4o)
    │                               ├── Filesystem MCP  (reads local files)
    │                               └── GitHub MCP      (finds real examples)
    │
    ├── library / repo question →  Repo Search Agent (GPT-4o)
    │                               ├── GitHub MCP      (searches repos)
    │                               └── Filesystem MCP  (saves examples)
    │
    └── error / concept / docs →   Web Research Agent (GPT-4o)
                                    ├── DuckDuckGo tool (live web search)
                                    └── Filesystem MCP  (saves reports)
    │
    ▼
Output guardrails (PII + length)
    │
    ▼
SQLiteSession → saves every turn to data/conversations.db
```

---

## Agents

| Agent | Model | Tools | Job |
|---|---|---|---|
| **Triage Agent** | GPT-4o-mini | — | Routes every request to the right specialist |
| **Code Review Agent** | GPT-4o | Filesystem MCP + GitHub MCP | Reads your files, reviews code, finds bugs |
| **Repo Search Agent** | GPT-4o | GitHub MCP + Filesystem MCP | Searches GitHub, reads real READMEs and source code |
| **Web Research Agent** | GPT-4o | DuckDuckGo + Filesystem MCP | Searches the live web, finds docs and solutions |

---

## MCP Servers

No tool functions written. Agents auto-discover tools from MCP servers at runtime.

| MCP Server | How installed | Tools available to agents |
|---|---|---|
| `@modelcontextprotocol/server-filesystem` | `npx -y` (auto) | `read_file`, `write_file`, `list_directory`, `search_files` |
| `@modelcontextprotocol/server-github` | `npx -y` (auto) | `search_repositories`, `search_code`, `get_file_contents`, `list_commits`, `get_issues` |

> Web search uses the `duckduckgo-search` Python package — no API key, no MCP server needed.

### Optional: Parallel web research

Set `WEB_SEARCH_PROVIDER=parallel` in your `.env` to use
[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
for web search and page fetching. It connects to `https://search.parallel.ai/mcp`
over Streamable HTTP using the existing OpenAI Agents SDK dependency.
No Parallel account or API key is needed. Anonymous search uses Fast mode and
has usage limits.

```env
WEB_SEARCH_PROVIDER=parallel
```

Start DevMind with the usual `python -m src.devmind.main` command. Try:

```text
Find the current OpenAI Agents SDK handoff documentation, fetch the relevant page, and explain how to pass structured handoff data.
```

The Web Research Agent discovers `web_search` and `web_fetch` from Parallel;
its filesystem tools still save reports. This selection replaces the DuckDuckGo
function tool for web research, avoiding duplicate `web_search` tool names.
The OpenAI and GitHub credentials in the setup below are still required.
If Parallel is unavailable, startup or the tool call reports an error; it does
not silently switch providers. Set `WEB_SEARCH_PROVIDER=duckduckgo` or remove
the variable to return to the default DuckDuckGo tool.

---

## Guardrails

| Guard | Type | Blocks |
|---|---|---|
| `empty_input` | Input | Blank or near-empty messages |
| `jailbreak` | Input | "ignore instructions", "DAN mode", etc. |
| `path_traversal` | Input | Attempts to read `/etc/passwd`, `~/.ssh`, `.env` files |
| `pii` | Output | Emails, phone numbers, API keys in responses |
| `length` | Output | Responses over 2000 characters |

---

## Memory

Every conversation turn is saved to `data/conversations.db` via `SQLiteSession`.

```
Turn 1: "review my auth file"      → found 2 issues
Turn 2: "fix the first issue"      → knows which issue you mean
Turn 3: "is that a common bug?"    → knows what "that" refers to
Turn 4: "save a full report"       → has the complete context
```

---

## Try These Questions

**Code Review**
```
review the file src/devmind/guardrails/input_guards.py and explain what each guard does
```

**Repo Search**
```
find the best open source Python project that uses multi-agent AI and show me a real code example
```

**Web Research**
```
what is the difference between openai agents sdk and langgraph? which one should a beginner use in 2025?
```

---

## Setup

### Requirements
- Python 3.11+
- Node.js 18+ (for `npx` — MCP servers run as subprocesses)
- OpenAI API key
- GitHub Personal Access Token

### Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-powered-dev-assistant
cd ai-powered-dev-assistant

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
FS_ROOT_PATH=/Users/your-username
SESSION_ID=devmind-user
DB_PATH=data/conversations.db
```

Get your keys:
- **OpenAI**: [platform.openai.com](https://platform.openai.com) → API Keys
- **GitHub PAT**: [github.com/settings/tokens](https://github.com/settings/tokens) — scopes: `repo`, `read:org`

### Run

```bash
python -m src.devmind.main
```

The first run downloads MCP server packages via npx (takes ~30 seconds). Subsequent runs are instant.

---

## Project Structure

```
ai-powered-dev-assistant/
├── README.md
├── CLAUDE.md
├── requirements.txt
├── .gitignore
├── assets/
│   └── screenshots/             ← place demo screenshots here
├── data/                        ← SQLite session DB (gitignored)
└── src/
    └── devmind/
        ├── main.py              ← CLI entry point
        ├── config.py            ← env vars + constants
        ├── agents/
        │   ├── triage_agent.py
        │   ├── code_review_agent.py
        │   ├── repo_search_agent.py
        │   └── web_research_agent.py
        ├── guardrails/
        │   ├── input_guards.py  ← empty, jailbreak, path_traversal
        │   └── output_guards.py ← pii, length
        ├── mcp/
        │   └── servers.py       ← MCPServerStdio factory functions
        ├── tools/
        │   └── web_search.py    ← DuckDuckGo function tool
        └── session/
            └── memory.py        ← SQLiteSession factory
```

---

## SDK Concepts Demonstrated

| Concept | Where |
|---|---|
| `MCPServerStdio` | `mcp/servers.py` — connect agents to MCP servers over stdio |
| Multi-MCP per agent | `code_review_agent.py` — Filesystem + GitHub on one agent |
| Tool auto-discovery | Agents discover MCP tools at runtime, no manual registration |
| `handoff()` with `input_type` | `triage_agent.py` — structured metadata on every handoff |
| `@input_guardrail` | `guardrails/input_guards.py` — tripwire pattern |
| `@output_guardrail` | `guardrails/output_guards.py` — tripwire pattern |
| `SQLiteSession` | `session/memory.py` — persistent cross-turn memory |
| `@function_tool` | `tools/web_search.py` — custom Python tool alongside MCP |

---

*Built with [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)*
