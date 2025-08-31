#!/usr/bin/env python3
"""
Script demo per dokkument
Mostra le funzionalità principali dell'applicazione
"""

import tempfile
from pathlib import Path
import sys
import os

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from dokkument.main import DokkumentApp
    from dokkument.parser import DokkFileScanner
    from dokkument.link_manager import LinkManager
except ImportError as e:
    print(f"Errore importazione moduli dokkument: {e}")
    print("Assicurati di essere nella directory corretta del progetto")
    sys.exit(1)


def create_demo_files(temp_dir):
    """Crea file .dokk di esempio per la demo"""

    # File principale di documentazione
    main_dokk = temp_dir / "documentation.dokk"
    main_dokk.write_text("""# Documentazione Principale del Progetto
"Documentazione API" -> "https://api.example.com/docs"
"Wiki del Team" -> "https://wiki.example.com"
"Guidelines di Sviluppo" -> "https://dev.example.com/guidelines"
"Dashboard Monitoring" -> "https://grafana.example.com"
""")

    # File per i repository
    repo_dokk = temp_dir / "repositories.dokk"
    repo_dokk.write_text("""# Repository e Codice Sorgente
"Repository Principale" -> "https://github.com/company/main-app"
"Repository Frontend" -> "https://github.com/company/frontend"
"Repository API" -> "https://github.com/company/api-server"
""")

    # File per strumenti esterni
    tools_dokk = temp_dir / "tools.dokk"
    tools_dokk.write_text("""# Strumenti e Servizi Esterni
"Jira Project" -> "https://company.atlassian.net/browse/PROJ"
"Confluence Space" -> "https://company.atlassian.net/wiki/spaces/DEV"
"Slack Channel" -> "https://company.slack.com/channels/development"
"CI/CD Pipeline" -> "https://jenkins.example.com/job/main-pipeline"
""")

    return [main_dokk, repo_dokk, tools_dokk]


def demo_scanning():
    """Demo della funzionalità di scansione"""
    print("🔍 Demo: Scansione file .dokk")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Crea file demo
        demo_files = create_demo_files(temp_path)
        print(f"✅ Creati {len(demo_files)} file .dokk in {temp_path}")

        # Scansiona directory
        scanner = DokkFileScanner()
        results = scanner.scan_directory(temp_path)

        print(f"📂 Trovati {len(results)} file .dokk:")
        for file_path, entries in results.items():
            print(f"  📄 {file_path.name}: {len(entries)} link")
            for i, entry in enumerate(entries, 1):
                print(f"    {i}. {entry.description}")

        print(
            f"\n📊 Totale: {sum(len(entries) for entries in results.values())} link trovati"
        )


def demo_link_manager():
    """Demo del LinkManager con colori e statistiche"""
    print("\n🎨 Demo: LinkManager con colori e statistiche")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Crea file demo
        create_demo_files(temp_path)

        # Usa LinkManager
        link_manager = LinkManager()
        total_links = link_manager.scan_for_links(temp_path)

        print(f"✅ Scansionati {total_links} link")

        # Mostra statistiche
        stats = link_manager.get_statistics()
        print(f"📊 Statistiche:")
        print(f"  • File: {stats['total_files']}")
        print(f"  • Link: {stats['total_links']}")
        print(f"  • Domini unici: {stats['unique_domains']}")

        # Demo filtro
        print(f"\n🔍 Demo filtro - ricerca 'API':")
        api_entries = link_manager.filter_entries("API")
        for entry in api_entries:
            print(f"  ✓ {entry.description} -> {entry.url}")

        # Demo validazione
        print(f"\n🔒 Demo validazione link:")
        invalid_links = link_manager.validate_all_links()
        if invalid_links:
            print(f"  ⚠️  Trovati {len(invalid_links)} link non validi")
        else:
            print(f"  ✅ Tutti i link sono validi")


def demo_export():
    """Demo delle funzionalità di esportazione"""
    print("\n📤 Demo: Esportazione in vari formati")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Crea file demo
        create_demo_files(temp_path)

        # Usa LinkManager
        link_manager = LinkManager()
        link_manager.scan_for_links(temp_path)

        # Demo esportazione JSON
        print("📄 Esportazione JSON (primi 200 caratteri):")
        json_export = link_manager.export_to_format("json")
        print(f"  {json_export[:200]}...")

        # Demo esportazione Markdown
        print("\n📝 Esportazione Markdown (prime 10 righe):")
        md_export = link_manager.export_to_format("markdown")
        md_lines = md_export.split("\n")[:10]
        for line in md_lines:
            print(f"  {line}")
        if len(md_export.split("\n")) > 10:
            print("  ...")


def demo_cli_display():
    """Demo del CLIDisplay"""
    print("\n🖥️  Demo: Interfaccia CLI")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Crea file demo
        create_demo_files(temp_path)

        # Usa componenti principali
        link_manager = LinkManager()
        total_links = link_manager.scan_for_links(temp_path)

        # Import here to avoid circular imports
        from dokkument.cli_display import CLIDisplay

        cli_display = CLIDisplay(link_manager)

        print("📋 Simulazione interfaccia utente:")
        print()

        # Simula header
        cli_display.print_header("dokkument Demo")

        # Simula risultati scansione
        stats = link_manager.get_statistics()
        cli_display.print_scan_results(stats["total_links"], stats["total_files"])

        # Simula menu (prime 3 entry)
        entries = link_manager.get_all_entries()[:3]
        if entries:
            print("📋 Preview menu (prime 3 entry):")
            for i, entry in enumerate(entries, 1):
                colored_desc = link_manager.get_colored_description(entry)
                print(f"[{i:2d}] {colored_desc}")
                print(f"     {entry.url}")

        # Simula statistiche
        print("\n📊 Statistiche complete:")
        cli_display.print_statistics(stats)


def main():
    """Funzione principale demo"""
    print("🚀 DOKKUMENT - Demo delle Funzionalità")
    print("=" * 60)
    print("Questa demo mostra le principali funzionalità di dokkument")
    print("senza richiedere file .dokk preesistenti.\n")

    try:
        # Esegui tutte le demo
        demo_scanning()
        demo_link_manager()
        demo_export()
        demo_cli_display()

        print("\n✅ Demo completata con successo!")
        print("\nPer usare dokkument:")
        print("  1. Crea file .dokk nella tua directory di progetto")
        print("  2. Esegui 'dokkget' per la modalità interattiva")
        print("  3. Usa 'dokkget --help' per vedere tutte le opzioni")

    except Exception as e:
        print(f"\n❌ Errore durante la demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
