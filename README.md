# agent-shelf

Libreria centralizzata di agenti AI aziendali. Ogni agente è composto da un system prompt, skills opzionali e configurazione di eventuali MCP server esterni.

Un server MCP locale legge questa repository via GitHub API e la espone come tool calls a VS Code / GitHub Copilot Agent Mode.

```
Copilot Agent Mode  ←→  MCP Server (locale)  ←→  GitHub API  ←→  agent-shelf repo
```

## Tool calls disponibili

| Tool | Descrizione |
|---|---|
| `list_agents` | Lista tutti gli agenti con metadati (id, name, version, category, description, author) |
| `get_agent` | Restituisce system prompt + skills disponibili + config MCP per un agente specifico |
| `get_skill` | Carica una skill extended on-demand durante una sessione attiva |
| `configure_workspace` | Scrive `.vscode/mcp.json` nel workspace corrente con la config MCP dell'agente |

## Agenti disponibili

| ID | Nome | Categoria | Descrizione |
|----|------|-----------|-------------|
| [`code-reviewer`](agents/code-reviewer/README.md) | Code Reviewer | engineering | Revisione codice con focus su qualità, sicurezza e best practice |
| [`looker-analyst`](agents/looker-analyst/README.md) | Looker Analyst | analytics | Analisi dati su Looker con focus su metriche business |
| [`notion-writer`](agents/notion-writer/README.md) | Notion Writer | writing | Creazione e aggiornamento di pagine Notion con struttura coerente |

Per i dettagli di ogni agente (skills, MCP server, variabili d'ambiente) consulta il `README.md` nella cartella dell'agente.

## Struttura della repository

```
agents/
└── <agent-id>/
    ├── agent.json          # metadati e manifest delle skills
    ├── system-prompt.md    # istruzioni principali (sempre caricate)
    └── skills/
        └── <skill>.md     # conoscenza specializzata (caricata on-demand)

mcp-server/
├── main.py                 # entry point FastMCP; espone app ASGI per uvicorn
├── pyproject.toml          # dipendenze: fastmcp, httpx, pydantic-settings, uvicorn
├── Dockerfile              # immagine python:3.11-slim, porta 8000
├── providers/              # adapter per provider Git (interfaccia astratta + implementazioni)
│   ├── base.py             # ABC GitProvider (get_file, list_directory)
│   ├── github.py           # GitHub REST API v2022-11-28 via httpx
│   └── factory.py          # crea il provider dalla variabile GIT_PROVIDER
└── tools/                  # logica tool calls separata in moduli
    ├── list_agents.py
    ├── get_agent.py        # include _build_vscode_mcp_config per http e stdio
    ├── get_skill.py
    └── configure_workspace.py
```

### Schema `agent.json`

```jsonc
{
  "id": "string",               // corrisponde al nome della cartella
  "name": "string",             // nome leggibile
  "version": "string",          // semver
  "category": "string",         // es. engineering, analytics, writing
  "description": "string",
  "author": "string",
  "skills": {
    "core": ["system-prompt.md"],          // sempre caricati in get_agent
    "extended": ["skills/<name>.md"]       // caricabili on-demand con get_skill
  },
  "mcp_servers": [              // array vuoto se non richiesti
    {
      "name": "string",
      "type": "http | stdio",
      "url": "string",          // solo per type: http
      "auth": { "type": "bearer", "header": "Authorization", "env": "VAR_NAME" },
      "command": "string",      // solo per type: stdio
      "args": ["string"],
      "env_required": ["VAR_NAME"],
      "env_optional": { "VAR_NAME": "default" }
    }
  ]
}
```

## Setup del MCP Server

### Prerequisiti

- Docker (opzione consigliata) oppure Python 3.11+
- GitHub Personal Access Token con scope `Contents: Read` (fine-grained) o `repo` (classic)

---

### Opzione A — Docker (consigliata)

Il server espone un endpoint HTTP su porta 8000 gestito da **uvicorn**.

#### 1. Build dell'immagine

```bash
cd mcp-server
docker build -t agent-shelf-mcp:latest .
```

#### 2. Avvio del container

```bash
docker run -d --name agent-shelf \
  -p 8000:8000 \
  --env-file mcp-server/.env \
  -v "/path/ai/tuoi/progetti:/workspaces" \
  agent-shelf-mcp:latest
```

Il volume `-v` monta la cartella dei tuoi progetti nel container come `/workspaces`, necessario perché il tool `configure_workspace` possa scrivere `.vscode/mcp.json` nei workspace locali.

Su Windows:
```powershell
docker run -d --name agent-shelf `
  -p 8000:8000 `
  --env-file mcp-server/.env `
  -v "C:\tuoi\progetti:/workspaces" `
  agent-shelf-mcp:latest
```

Porta e host personalizzabili via variabili d'ambiente: `-e PORT=9000 -e HOST=127.0.0.1`.

#### 3. Configurazione VS Code

Aggiungi al tuo file `~/.vscode/mcp.json` (crealo se non esiste):

```json
{
  "servers": {
    "agent-shelf": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Nessun token in questo file: le credenziali GitHub vivono nel container, non nel client.

#### 4. Test con MCP Inspector via Docker

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

---

### Opzione B — Python diretto

#### 1. Installazione

```bash
cd mcp-server
pip install -e .
```

#### 2. Configurazione VS Code

Aggiungi al tuo file `~/.vscode/mcp.json`:

```json
{
  "servers": {
    "agent-shelf": {
      "command": "python",
      "args": ["-m", "main"],
      "cwd": "/percorso/assoluto/a/agent-shelf/mcp-server",
      "env": {
        "GIT_PROVIDER": "github",
        "GITHUB_TOKEN": "${input:githubToken}",
        "GITHUB_OWNER": "nome-organizzazione",
        "GITHUB_REPO": "agent-shelf",
        "GITHUB_BRANCH": "main"
      }
    }
  },
  "inputs": [
    {
      "id": "githubToken",
      "type": "promptString",
      "description": "GitHub Personal Access Token (scope: contents:read)",
      "password": true
    }
  ]
}
```

Sostituisci `/percorso/assoluto/a/agent-shelf/mcp-server` con il path reale.

#### 3. Test con MCP Inspector

```bash
cd mcp-server
npx @modelcontextprotocol/inspector python -m main
```

### Variabili d'ambiente

| Variabile | Richiesta | Default | Descrizione |
|-----------|-----------|---------|-------------|
| `GIT_PROVIDER` | No | `github` | Provider Git (attualmente: `github`) |
| `GITHUB_TOKEN` | Sì | — | Personal Access Token (scope `contents:read`) |
| `GITHUB_OWNER` | Sì | — | Username o organizzazione GitHub |
| `GITHUB_REPO` | Sì | — | Nome della repository |
| `GITHUB_BRANCH` | No | `main` | Branch da leggere |
| `HOST` | No | `0.0.0.0` | Host su cui uvicorn ascolta |
| `PORT` | No | `8000` | Porta su cui uvicorn ascolta |

## Aggiungere un nuovo agente

1. Crea la cartella `agents/<agent-id>/` — l'ID deve corrispondere esattamente al nome cartella
2. Scrivi `agent.json` seguendo lo schema (vedi agenti esistenti come riferimento)
3. Scrivi `system-prompt.md` con le istruzioni principali dell'agente
4. Aggiungi le skills in `skills/<nome>.md` e referenziale in `agent.json`
5. Apri una Pull Request — la GitHub Action validerà automaticamente la struttura prima del merge
