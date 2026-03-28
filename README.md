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

### `list_agents`
Restituisce un array JSON con i campi `id`, `name`, `version`, `category`, `description`, `author` per ogni agente. Non include il contenuto dei system prompt o delle skills.

### `get_agent`
Restituisce un oggetto JSON con:
- `system_prompt` — contenuto delle skills core concatenate (da iniettare come system prompt)
- `available_skills` — elenco delle skills extended caricabili on-demand
- `mcp_servers` — configurazione VSCode-ready dei server MCP esterni richiesti dall'agente
- `metadata` — id, name, version, category

Se `mcp_servers` non è vuoto, il chiamante deve configurare il server prima di avviare la sessione (vedi workflow per tipo `http` e `stdio` nella docstring del tool).

### `get_skill`
Carica una skill extended on-demand. `skill_name` è il nome del file senza path e senza `.md` (es. `python-review` per `skills/python-review.md`).

### `configure_workspace`
Scrive la configurazione MCP dell'agente nel file `.vscode/mcp.json` della cartella di lavoro corrente, evitando la configurazione manuale. Esegue un merge non distruttivo: se il file esiste già, aggiunge solo il nuovo server senza rimuovere quelli presenti. Se `credentials` è fornito, aggiunge `.vscode/mcp.json` al `.gitignore` del workspace per evitare commit accidentali.

**Nota sul `workspace_path`**: il path deve essere nel formato del container (`/workspaces/<nome-cartella>`). Richiede che il container sia avviato con il volume `-v "<cartella-progetti-host>:/workspaces"`.

## Agenti disponibili

| ID | Nome | Categoria | MCP Server | Descrizione |
|----|------|-----------|------------|-------------|
| `code-reviewer` | Code Reviewer | engineering | — | Revisione codice con focus su qualità, sicurezza e best practice |
| `looker-analyst` | Looker Analyst | analytics | `looker-docker` (stdio) | Analisi dati su Looker con focus su metriche business |
| `notion-writer` | Notion Writer | writing | `notion` (http) | Creazione e aggiornamento di pagine Notion con struttura coerente |

### code-reviewer

- **Skills core**: `system-prompt.md`
- **Skills extended**: `python-review`, `security-audit`, `go-patterns`
- **MCP servers**: nessuno

### looker-analyst

- **Skills core**: `system-prompt.md`
- **Skills extended**: `looker-usage`, `metrics-guide`
- **MCP servers**: `looker-docker` (stdio, Docker)
  - Variabili **obbligatorie**: `LOOKER_CLIENT_ID`, `LOOKER_CLIENT_SECRET`
  - Variabili opzionali: `LOOKER_BASE_URL` (default: `https://jakala.cloud.looker.com/`), `LOOKER_VERIFY_SSL` (default: `true`)
  - Immagine Docker richiesta: `looker-mcp-toolbox`

### notion-writer

- **Skills core**: `system-prompt.md`
- **Skills extended**: `notion-structure`, `writing-style`
- **MCP servers**: `notion` (http, bearer auth)
  - Variabili **obbligatorie**: `NOTION_API_KEY`
  - Endpoint: `https://mcp.notion.com/mcp`
  - L'autenticazione avviene tramite header `Authorization: Bearer <token>`

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
