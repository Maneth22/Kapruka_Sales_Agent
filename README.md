# Kapruka Sales Agent

An AI-powered sales assistant for [Kapruka](https://www.kapruka.com) — Sri Lanka's online marketplace. Uses a multi-agent pipeline (Interaction → Request Handler → Validation) with Google Gemini to handle product searches, orders, delivery checks, and more via MCP tools.

## Architecture

```
User (Browser) ──WebSocket──┐
                            ▼
┌──────────────────────────────────────────┐
│  Flask + SocketIO (backend/main.py)      │
├──────────────────────────────────────────┤
│  PipelineQueue (threading.Semaphore)     │
│    └─ GeminiAgent (orchestrator)         │
│         ├─ InteractionAgent              │
│         ├─ RequestHandlerAgent           │
│         └─ ValidationAgent               │
│              └─ GeminiRequestQueue        │
│                   └─ genai.Client         │
├──────────────────────────────────────────┤
│  KaprukaMCPClient (async background)     │
│    └─ MCP Server (kapruka.com)           │
└──────────────────────────────────────────┘
```

## Project Structure

```
Kapruka_Sales_Agent/
├── backend/
│   ├── agents/           # Gemini-powered agent pipeline
│   │   ├── base.py               # Abstract BaseAgent
│   │   ├── gemini_agent.py       # Orchestrator
│   │   ├── interaction_agent.py  # Customer chat agent
│   │   ├── request_handler_agent.py  # Tool-call builder
│   │   └── validation_agent.py   # Response validator
│   ├── core/
│   │   ├── config.py        # Settings from .env
│   │   ├── gemini_queue.py  # Gemini API rate-limiter + retry
│   │   ├── pipeline_queue.py # Pipeline-level concurrency gate
│   │   ├── chat_store.py    # In-memory chat history
│   │   └── security.py      # JWT auth, bcrypt
│   ├── mcp_client/          # MCP (Model Context Protocol) client
│   │   ├── client.py        # Async MCP connection
│   │   └── tools.py         # Tool declarations for Gemini
│   ├── prompts/             # System prompts for each agent
│   ├── routes/
│   │   ├── chat.py          # SocketIO event handlers
│   │   └── auth.py          # Login/register REST endpoints
│   └── models/
│       └── schemas.py       # Request/response models
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # useChat (SocketIO + state)
│   │   └── api/             # REST API client
│   └── package.json
├── tests/
│   ├── test_helpers.py      # JSON extraction tests
│   ├── test_pipeline.py     # Agent pipeline unit tests
│   └── test_mcp_tools.py    # Live MCP integration tests
├── .env                     # Environment variables
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Gemini API key

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set GEMINI_API_KEY and adjust other settings

# Run the server
python backend/main.py
# Starts on http://localhost:8080
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development server (port 3000, proxies to backend)
npm run dev

# Production build
npm run build
npm run preview     # serve built files
```

### Docker

```bash
docker-compose up --build
# Serves everything on port 8080
```

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Google Gemini API key (required) |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model name |
| `MCP_SERVER_URL` | `https://mcp.kapruka.com/mcp` | MCP server endpoint |
| `JWT_SECRET` | `change-me` | Secret for JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_HOURS` | `24` | Token lifetime |
| `ADMIN_USERNAME` | `admin` | Default admin user |
| `ADMIN_PASSWORD` | — | Admin password (required) |
| `HOST` | `0.0.0.0` | Backend host |
| `PORT` | `8080` | Backend port |
| `PIPELINE_MAX_CONCURRENCY` | `1` | Max simultaneous agent pipelines |
| `PIPELINE_INTERVAL_MS` | `3000` | Min gap (ms) between pipelines |

## Testing

```bash
# Unit tests (mocked Gemini, no API key needed)
python -m pytest tests/test_pipeline.py tests/test_helpers.py -v

# MCP integration tests (requires MCP server connection)
python tests/test_mcp_tools.py                     # all tools
python tests/test_mcp_tools.py search              # single tool
python tests/test_mcp_tools.py --verbose           # full responses
python tests/test_mcp_tools.py --timeout 15        # connection timeout

# Run all
python -m pytest tests/ -v
```

## Agent Pipeline

Each user message runs through up to 4 Gemini calls controlled by `PipelineQueue` (max 1 concurrent pipeline with configurable interval):

```
1. InteractionAgent.chat()       → Understand request, extract JSON requirements
2. RequestHandlerAgent.build()   → Convert requirements to MCP tool call
3. MCP Client call_tool()        → Execute against Kapruka MCP server
4. ValidationAgent.validate()    → Check if response satisfies user
   └─ satisfied? → InteractionAgent.present_results()
   └─ not satisfied → retry with refined params (up to 2 retries)
   └─ exhausted → InteractionAgent.explain_limitations()
```

Agent outputs are streamed to the frontend via the `agent_output` SocketIO event and displayed in collapsible cards labelled by agent name.

## Frontend Stack

- **React 18** + **Vite 6**
- **Mantine UI** v7 — all components and theming
- **Socket.IO** — real-time chat and agent output streaming
- **react-router-dom** — login/chat routing
