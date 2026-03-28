# Notion Writer

| Campo | Valore |
|-------|--------|
| **ID** | `notion-writer` |
| **Categoria** | writing |
| **Versione** | 1.0.0 |
| **Autore** | team-it |
| **MCP Server** | `notion` (http, bearer auth) |

Agente specializzato nella creazione e gestione di contenuti su Notion. Produce documenti strutturati, coerenti con le convenzioni del workspace aziendale, interagendo direttamente con l'API Notion tramite MCP.

## Cosa fa

- Crea nuove pagine Notion da descrizioni o contenuti grezzi
- Organizza l'informazione con i blocchi appropriati (callout, toggle, tabelle, database inline, intestazioni)
- Aggiorna pagine esistenti mantenendo struttura e stile coerenti
- Supporta documentazione tecnica: runbook, ADR, spec di prodotto, post-mortem
- Configura proprietà, relazioni e formule nei database Notion

## Principi di struttura

- Ogni documento inizia con **titolo chiaro + TL;DR** (max 2-3 righe)
- Scannerizzabile: intestazioni e bullet point devono bastare per capire il contenuto
- Progressione logica: contesto → situazione attuale → decisioni/azioni → prossimi passi
- Le sezioni "chi fa cosa entro quando" non devono mai mancare

## Skills

### Core (sempre attive)

| File | Contenuto |
|------|-----------|
| `system-prompt.md` | Istruzioni principali, principi di struttura, tipi di documento |

### Extended (on-demand con `get_skill`)

| Skill | Quando usarla |
|-------|---------------|
| `notion-structure` | Template strutturali per ogni tipo di documento (progetto, meeting notes, ADR, runbook) |
| `writing-style` | Convenzioni di stile e tono per i diversi contesti aziendali |

## MCP Server

Questo agente richiede il server MCP ufficiale di Notion per interagire con il workspace.

| Parametro | Valore |
|-----------|--------|
| Tipo | `http` |
| Endpoint | `https://mcp.notion.com/mcp` |
| Autenticazione | Bearer token (`Authorization: Bearer <token>`) |

### Variabili d'ambiente

| Variabile | Obbligatoria | Note |
|-----------|-------------|------|
| `NOTION_API_KEY` | Sì | Integration token Notion (Internal Integration) |

## Come attivarlo

```
list_agents → get_agent("notion-writer")
```

Il tool `get_agent` restituisce la configurazione `mcp.json` pronta per VS Code con `${input:notion-api-key}`. VS Code chiederà il token al primo utilizzo e lo salverà nel keychain del sistema operativo.

Per server HTTP la configurazione va scritta in `.vscode/mcp.json` del workspace corrente — VS Code la rileva automaticamente. Esegui poi **MCP: List Servers** dal Command Palette per confermare l'attivazione.
