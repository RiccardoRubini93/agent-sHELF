import json
import os
from pathlib import Path
from providers.base import GitProvider
from tools.get_agent import _build_vscode_mcp_config

_GITIGNORE_MARKER = "# agent-shelf managed"


async def configure_workspace(
    provider: GitProvider,
    agent_id: str,
    workspace_path: str,
    credentials: dict | None = None,
) -> str:
    """
    Scrive la configurazione MCP dell'agente nel file .vscode/mcp.json
    della cartella di lavoro corrente, evitando la configurazione manuale.

    Usare questo tool subito dopo get_agent quando mcp_servers non è vuoto.
    workspace_path è il path assoluto della cartella root del progetto corrente.

    Workflow credenziali:
    - Se mcp_servers contiene env_required non vuoto, PRIMA di chiamare questo
      tool chiedere all'utente i valori di quelle variabili nel chat.
    - Passare i valori raccolti come dizionario nel parametro 'credentials'.
      Esempio: credentials={"LOOKER_CLIENT_ID": "...", "LOOKER_CLIENT_SECRET": "..."}
    - Se credentials è fornito, i valori vengono scritti direttamente nel file
      e VS Code avvierà il server senza ulteriori prompt all'utente.
    - Se credentials è omesso, vengono scritti ${input:...} e VS Code chiederà
      i valori al primo avvio (salvandoli nel keychain del SO).

    Sicurezza:
    - Se credentials è fornito, .vscode/mcp.json viene aggiunto automaticamente
      al .gitignore del workspace per evitare commit accidentali delle credenziali.

    Esegue un merge non distruttivo: se .vscode/mcp.json esiste già,
    aggiunge solo il nuovo server senza rimuovere quelli già presenti.

    Dopo la chiamata, per server stdio l'utente deve eseguire
    'MCP: List Servers' dal Command Palette di VS Code.
    Per server HTTP il rilevamento è automatico.
    """
    raw_manifest = await provider.get_file(f"agents/{agent_id}/agent.json")
    manifest = json.loads(raw_manifest)

    mcp_servers = manifest.get("mcp_servers", [])
    if not mcp_servers:
        return json.dumps({
            "status": "skipped",
            "reason": f"L'agente '{agent_id}' non richiede server MCP esterni.",
        }, ensure_ascii=False, indent=2)

    new_config = _build_vscode_mcp_config(mcp_servers)

    # Sostituisci ${input:...} con valori reali se le credenziali sono fornite
    if credentials:
        for server_cfg in new_config.get("servers", {}).values():
            env = server_cfg.get("env", {})
            for key, value in env.items():
                # Trova la variabile corrispondente nelle credenziali fornite
                if key in credentials:
                    env[key] = credentials[key]
        # Rimuovi gli inputs già soddisfatti dalle credenziali
        satisfied_ids = set()
        for server_cfg in manifest.get("mcp_servers", []):
            for env_key in server_cfg.get("env_required", []):
                if env_key in credentials:
                    satisfied_ids.add(env_key.lower().replace("_", "-"))
        new_config["inputs"] = [
            i for i in new_config.get("inputs", [])
            if i["id"] not in satisfied_ids
        ]

    # Rimuove il _note di documentazione prima di scrivere
    for server_cfg in new_config.get("servers", {}).values():
        server_cfg.pop("_note", None)

    workspace_root = Path(workspace_path)
    vscode_dir = workspace_root / ".vscode"
    mcp_json_path = vscode_dir / "mcp.json"

    # Verifica che workspace_path esista nel filesystem del container.
    # Se non esiste, la cartella non è nel volume mount → il file verrebbe
    # scritto nel filesystem interno del container e andrebbe perso.
    if not workspace_root.exists():
        folder_name = workspace_root.name
        return json.dumps({
            "status": "error",
            "reason": (
                f"Il path '{workspace_path}' non esiste nel filesystem del container. "
                f"La cartella non è inclusa nel volume mount. "
                f"Usa il path nel formato '/workspaces/<nome-cartella>' "
                f"(es. '/workspaces/{folder_name}'). "
                f"Assicurati che il container sia avviato con: "
                f"-v \"<cartella-progetti-host>:/workspaces\""
            ),
            "suggested_path": f"/workspaces/{folder_name}",
        }, ensure_ascii=False, indent=2)

    # Merge non distruttivo con configurazione esistente
    existing: dict = {"servers": {}}
    if mcp_json_path.exists():
        try:
            existing = json.loads(mcp_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    merged_servers = {**existing.get("servers", {}), **new_config["servers"]}
    existing_inputs = existing.get("inputs", [])
    new_input_ids = {i["id"] for i in new_config.get("inputs", [])}
    merged_inputs = [i for i in existing_inputs if i["id"] not in new_input_ids]
    merged_inputs += new_config.get("inputs", [])

    final: dict = {"servers": merged_servers}
    if merged_inputs:
        final["inputs"] = merged_inputs

    vscode_dir.mkdir(parents=True, exist_ok=True)
    mcp_json_path.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Se le credenziali sono in chiaro, proteggi il file con .gitignore
    gitignore_updated = False
    if credentials:
        gitignore_updated = _ensure_gitignore(workspace_path, ".vscode/mcp.json")

    needs_reload = any(
        s.get("type", "stdio") == "stdio"
        for s in new_config["servers"].values()
    )
    credentials_mode = "inline (credenziali scritte direttamente)" if credentials else "input-prompt (VS Code chiederà al primo avvio)"

    return json.dumps({
        "status": "ok",
        "file": str(mcp_json_path),
        "servers_added": list(new_config["servers"].keys()),
        "credentials_mode": credentials_mode,
        "gitignore_updated": gitignore_updated,
        "next_step": (
            "Esegui 'MCP: List Servers' dal Command Palette di VS Code per attivare il server."
            if needs_reload else
            "Server HTTP rilevato automaticamente da VS Code."
        ),
    }, ensure_ascii=False, indent=2)


def _ensure_gitignore(workspace_path: str, rule: str) -> bool:
    """Aggiunge 'rule' al .gitignore del workspace se non già presente."""
    gitignore_path = Path(workspace_path) / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if rule in content:
            return False
        updated = content.rstrip("\n") + f"\n\n{_GITIGNORE_MARKER}\n{rule}\n"
    else:
        updated = f"{_GITIGNORE_MARKER}\n{rule}\n"
    gitignore_path.write_text(updated, encoding="utf-8")
    return True


    mcp_servers = manifest.get("mcp_servers", [])
    if not mcp_servers:
        return json.dumps({
            "status": "skipped",
            "reason": f"L'agente '{agent_id}' non richiede server MCP esterni.",
        }, ensure_ascii=False, indent=2)

    new_config = _build_vscode_mcp_config(mcp_servers)

    # Rimuove il _note dai server stdio prima di scrivere
    for server in new_config.get("servers", {}).values():
        server.pop("_note", None)

    vscode_dir = Path(workspace_path) / ".vscode"
    mcp_json_path = vscode_dir / "mcp.json"

    # Merge non distruttivo con configurazione esistente
    existing: dict = {"servers": {}}
    if mcp_json_path.exists():
        try:
            existing = json.loads(mcp_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass  # file corrotto → lo sovrascriviamo

    merged_servers = {**existing.get("servers", {}), **new_config["servers"]}
    merged_inputs = existing.get("inputs", [])
    new_input_ids = {i["id"] for i in new_config.get("inputs", [])}
    merged_inputs = [i for i in merged_inputs if i["id"] not in new_input_ids]
    merged_inputs += new_config.get("inputs", [])

    final: dict = {"servers": merged_servers}
    if merged_inputs:
        final["inputs"] = merged_inputs

    vscode_dir.mkdir(parents=True, exist_ok=True)
    mcp_json_path.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    needs_reload = any(
        s.get("type", "stdio") == "stdio"
        for s in new_config["servers"].values()
    )

    return json.dumps({
        "status": "ok",
        "file": str(mcp_json_path),
        "servers_added": list(new_config["servers"].keys()),
        "next_step": (
            "Esegui 'MCP: List Servers' dal Command Palette di VS Code per attivare il server."
            if needs_reload else
            "Server HTTP rilevato automaticamente da VS Code."
        ),
    }, ensure_ascii=False, indent=2)
