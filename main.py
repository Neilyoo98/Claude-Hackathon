#!/usr/bin/env python3
"""CLI entry point for Civic Signal Vault.

Web UI (Quizlet-style cards):  python serve.py  →  http://127.0.0.1:5050
"""

from __future__ import annotations

import random
import sys
import webbrowser

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from vault.config import ROOT
from vault.ingest import collect_all, refresh_database
from vault.recall import recall_high_energy, recall_low_energy
from vault.storage import load_items


def cmd_update() -> None:
    stats = refresh_database()
    print(
        f"Updated — RSS: {stats['rss_entries']} | Bills: {stats['legislation']} | "
        f"Merged: {stats['merged']} | Stored: {stats['stored_total']}"
    )
    if stats.get("congress_skipped_no_key"):
        print("(Congress skipped: set CONGRESS_API_KEY in .env or environment.)")


def cmd_recall(energy: str = "low", open_browser: bool = False) -> None:
    items = load_items()
    if not items:
        print("Vault is empty. Run: python main.py update")
        return
    random.seed()
    bundle = recall_low_energy(items) if energy == "low" else recall_high_energy(items)
    for i, item in enumerate(bundle.items, 1):
        d = (item.date or "")[:10] if item.date else "—"
        print(f"\n[{i}] {item.title}\n    {item.source} | {d} | #{item.topic}")
        print(f"    {item.url}")
        if open_browser:
            try:
                webbrowser.open(item.url)
            except Exception:
                pass
    if bundle.prompt:
        print(f"\n--- SYNTHESIS PROMPT ---\n{bundle.prompt}")


def cmd_preview() -> None:
    _, stats = collect_all()
    print(
        f"Preview — RSS: {stats['rss_entries']} | Bills: {stats['legislation']} "
        f"| congress_skipped_no_key={stats.get('congress_skipped_no_key', 0)}"
    )


def cmd_interactive() -> None:
    cmd_update()
    energy = input("\nEnergy level? [low/high] (default: low): ").strip().lower() or "low"
    if energy not in ("low", "high"):
        energy = "low"
    cmd_recall(energy)


def cmd_wizard() -> None:
    print("=== Civic Signal Vault Setup ===")
    key = input("Congress API key (press Enter to skip): ").strip()
    if key:
        env_path = ROOT / ".env"
        env_path.write_text(f"CONGRESS_API_KEY={key}\n", encoding="utf-8")
        print(f".env written to {env_path}.")
        # Reload env into process
        from vault import config as _cfg

        _cfg.load_dotenv_file()
    cmd_update()
    cmd_recall("low")


COMMANDS: dict[str, object] = {
    "update": cmd_update,
    "preview": cmd_preview,
    "interactive": cmd_interactive,
    "wizard": cmd_wizard,
}


def _parse_recall_args(argv: list[str]) -> tuple[str, bool]:
    energy = "low"
    open_browser = False
    i = 0
    while i < len(argv):
        if argv[i] == "--energy" and i + 1 < len(argv):
            energy = argv[i + 1].lower()
            i += 2
            continue
        if argv[i] == "--open-browser":
            open_browser = True
            i += 1
            continue
        i += 1
    if energy not in ("low", "high"):
        energy = "low"
    return energy, open_browser


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        cmd_interactive()
        return 0
    cmd = argv[0]
    if cmd == "recall":
        energy, ob = _parse_recall_args(argv[1:])
        cmd_recall(energy, ob)
        return 0
    if cmd in COMMANDS:
        fn = COMMANDS[cmd]
        if callable(fn):
            fn()
        return 0
    print(f"Unknown command. Use: {', '.join(sorted(COMMANDS))} or recall --energy low|high [--open-browser]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
