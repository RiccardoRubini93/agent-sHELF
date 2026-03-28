# Code Reviewer

| Campo | Valore |
|-------|--------|
| **ID** | `code-reviewer` |
| **Categoria** | engineering |
| **Versione** | 1.0.0 |
| **Autore** | team-it |
| **MCP Server** | — |

Agente specializzato nella revisione del codice sorgente. Analizza qualità, sicurezza e manutenibilità producendo feedback strutturato e costruttivo.

## Cosa fa

- Identifica code smell, anti-pattern e violazioni dei principi SOLID/DRY/KISS
- Rileva vulnerabilità OWASP Top 10 (injection, segreti hardcoded, broken access control, ecc.)
- Segnala inefficienze algoritmiche, memory leak e operazioni bloccanti
- Suggerisce miglioramenti a naming, struttura e test coverage
- Applica le convenzioni idiomatiche del linguaggio in uso

## Formato del feedback

Il feedback è sempre strutturato in tre livelli:

1. **Problemi critici** — da correggere prima del merge
2. **Miglioramenti consigliati** — qualità e leggibilità
3. **Osservazioni minori** — stile, preferenze, nice-to-have

Per ogni problema: descrizione, impatto concreto e snippet corretto con syntax highlighting.

## Skills

### Core (sempre attive)

| File | Contenuto |
|------|-----------|
| `system-prompt.md` | Istruzioni principali, formato output, comportamento generale |

### Extended (on-demand con `get_skill`)

| Skill | Quando usarla |
|-------|---------------|
| `python-review` | Codice Python: PEP 8, type hints, async, testing, anti-pattern |
| `security-audit` | Audit sicurezza approfondito: classificazione severità, OWASP checklist |
| `go-patterns` | Codice Go: error handling, concorrenza, goroutine, context |

## Come attivarlo

```
list_agents → get_agent("code-reviewer")
```

Se durante la sessione emerge codice in un linguaggio specifico o serve un audit di sicurezza, carica la skill corrispondente:

```
get_skill("code-reviewer", "python-review")
get_skill("code-reviewer", "security-audit")
get_skill("code-reviewer", "go-patterns")
```
