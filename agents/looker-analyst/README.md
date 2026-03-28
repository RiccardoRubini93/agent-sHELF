# Looker Analyst

| Campo | Valore |
|-------|--------|
| **ID** | `looker-analyst` |
| **Categoria** | analytics |
| **Versione** | 1.0.0 |
| **Autore** | team-it |
| **MCP Server** | `looker-docker` (stdio) |

Agente specializzato nell'analisi dei dati aziendali tramite Looker. Guida l'utente dall'interpretazione della domanda di business fino all'estrazione e lettura dei dati.

## Cosa fa

- Individua le Explore e View Looker più adatte alla domanda di business
- Aiuta a costruire query selezionando dimensioni, misure e filtri corretti
- Interpreta i risultati nel contesto business (trend, anomalie, confronti periodo su periodo)
- Supporta la scrittura e revisione di LookML (misure, dimensioni, Explore, PDT)
- Consiglia il tipo di visualizzazione più adatto (tabella, linee, heatmap, funnel)

## Principi di analisi

- Verifica sempre l'orizzonte temporale del dato (data di riferimento, fuso orario)
- Segmenta per cohort per evitare effetti di composizione del portfolio
- Metriche su periodi parziali (es. mese in corso) tendono ad apparire inferiori — normalizza o segnala
- Prima di concludere su una tendenza, verifica che non sia artefatto di un cambio di definizione

## Skills

### Core (sempre attive)

| File | Contenuto |
|------|-----------|
| `system-prompt.md` | Istruzioni principali, principi di analisi, ambito di competenza |

### Extended (on-demand con `get_skill`)

| Skill | Quando usarla |
|-------|---------------|
| `looker-usage` | Istruzioni dettagliate sull'uso dei tool MCP del server Looker |
| `metrics-guide` | Definizioni ufficiali delle metriche aziendali e reference in Looker |

## MCP Server

Questo agente richiede il server MCP `looker-docker` per interrogare Looker direttamente.

| Parametro | Valore |
|-----------|--------|
| Tipo | `stdio` |
| Comando | `docker run -i --rm looker-mcp-toolbox` |
| Immagine Docker | `looker-mcp-toolbox` |

### Variabili d'ambiente

| Variabile | Obbligatoria | Default |
|-----------|-------------|---------|
| `LOOKER_CLIENT_ID` | Sì | — |
| `LOOKER_CLIENT_SECRET` | Sì | — |
| `LOOKER_BASE_URL` | No | `https://jakala.cloud.looker.com/` |
| `LOOKER_VERIFY_SSL` | No | `true` |

## Come attivarlo

```
list_agents → get_agent("looker-analyst")
```

Il tool `get_agent` restituisce la configurazione MCP pronta. Per configurare il workspace automaticamente:

```
configure_workspace("looker-analyst", "/workspaces/<nome-cartella>", {
  "LOOKER_CLIENT_ID": "...",
  "LOOKER_CLIENT_SECRET": "..."
})
```

Poi esegui **MCP: List Servers** dal Command Palette di VS Code per attivare il server.
