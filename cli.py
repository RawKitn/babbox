# cli.py

import json
import subprocess
import typer
import uuid
from datetime import datetime
from jinja2 import Template
from pathlib import Path

app = typer.Typer()

DB_PATH = Path("commands.json")

def load_commands():
    with open(DB_PATH, "r") as f:
        return json.load(f)

@app.command()
def list_commands(category: str = typer.Option(None), tag: str = typer.Option(None)):
    """
    Liste les commandes avec filtres optionnels (catégorie, tag).
    """
    commands = load_commands()
    for cmd in commands:
        if category and cmd["category"] != category:
            continue
        if tag and tag not in cmd["tags"]:
            continue
        typer.echo(f"[{cmd['id']}] {cmd['title']} ({cmd['category']})")

@app.command()
def run(id: str):
    """
    Exécute une commande en remplissant les variables demandées.
    """
    commands = load_commands()
    for cmd in commands:
        if cmd["id"] == id:
            template = Template(cmd["command"])
            vars_needed = {}

            # Demande des variables
            for var in cmd["variables"]:
                val = typer.prompt(f"{var['description']} ({var['name']})", default=var.get("default", ""))
                vars_needed[var["name"]] = val

            final_cmd = template.render(**vars_needed)
            typer.echo(f"\n👉 Commande : {final_cmd}")
            confirm = typer.confirm("Lancer cette commande ?", default=False)
            if confirm:
                import os
                os.system(final_cmd)
            return

    typer.echo("❌ Commande non trouvée", err=True)

@app.command()
def add():
    """
    Ajoute une nouvelle commande à la boîte à outils.
    """
    typer.echo("🆕 Création d'une nouvelle commande")
    title = typer.prompt("Titre")
    command = typer.prompt("Commande (avec {{ variable }} si besoin)")
    category = typer.prompt("Catégorie")
    tags_str = typer.prompt("Tags (séparés par des virgules)")
    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

    variables = []
    has_vars = typer.confirm("La commande utilise-t-elle des variables ?", default=False)
    while has_vars:
        name = typer.prompt("Nom de la variable")
        description = typer.prompt("Description de cette variable")
        default = typer.prompt("Valeur par défaut (laisser vide si aucune)", default="")
        variables.append({
            "name": name,
            "description": description,
            "default": default
        })
        has_vars = typer.confirm("Ajouter une autre variable ?", default=False)

    # Création de l'objet
    now = datetime.utcnow().isoformat() + "Z"
    new_command = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "command": command,
        "category": category,
        "tags": tags,
        "variables": variables,
        "created_at": now,
        "updated_at": now
    }

    # Sauvegarde
    commands = load_commands()
    commands.append(new_command)
    with open(DB_PATH, "w") as f:
        json.dump(commands, f, indent=2)

    typer.echo(f"\n✅ Commande ajoutée avec l'ID : {new_command['id']}")

@app.command()
def edit(id: str):
    """
    Modifie une commande existante.
    """
    commands = load_commands()
    for cmd in commands:
        if cmd["id"] == id:
            typer.echo(f"📝 Modification de la commande '{cmd['title']}' (ID: {id})\n")

            cmd["title"] = typer.prompt("Titre", default=cmd["title"])
            cmd["command"] = typer.prompt("Commande", default=cmd["command"])
            cmd["category"] = typer.prompt("Catégorie", default=cmd["category"])
            tags_str = typer.prompt("Tags (séparés par des virgules)", default=",".join(cmd["tags"]))
            cmd["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            if typer.confirm("Souhaites-tu modifier les variables ?", default=False):
                new_vars = []
                while typer.confirm("Ajouter ou modifier une variable ?", default=False):
                    name = typer.prompt("Nom de la variable")
                    description = typer.prompt("Description")
                    default = typer.prompt("Valeur par défaut", default="")
                    new_vars.append({
                        "name": name,
                        "description": description,
                        "default": default
                    })
                cmd["variables"] = new_vars

            cmd["updated_at"] = datetime.utcnow().isoformat() + "Z"

            with open(DB_PATH, "w") as f:
                json.dump(commands, f, indent=2)

            typer.echo("✅ Commande mise à jour avec succès")
            return

    typer.echo(f"❌ Aucune commande avec l'ID '{id}' n'a été trouvée.", err=True)


@app.command()
def select(execute: bool = typer.Option(False, "--run", help="Exécuter la commande sélectionnée")):
    """
    Recherche et sélectionne une commande via fzf.
    """
    commands = load_commands()
    if not commands:
        typer.echo("⚠️ Aucune commande enregistrée.")
        raise typer.Exit()

    choices = [
        f"{cmd['id']} :: {cmd['title']} [{cmd['category']}] :: {', '.join(cmd['tags'])}"
        for cmd in commands
    ]

    try:
        result = subprocess.run(
            ["fzf"],
            input="\n".join(choices),
            text=True,
            capture_output=True
        )
    except FileNotFoundError:
        typer.echo("❌ fzf n'est pas installé. Installe-le avant d'utiliser cette commande.")
        raise typer.Exit(code=1)

    if result.returncode != 0:
        typer.echo("❌ Aucune sélection.")
        raise typer.Exit()

    selected_line = result.stdout.strip()
    selected_id = selected_line.split(" :: ")[0]

    if execute:
        typer.echo(f"🚀 Exécution de la commande {selected_id}...")
        run(selected_id)
    else:
        typer.echo(f"🆔 Commande sélectionnée : {selected_id}")


@app.command()
def tui():
    """
    Lance l'interface TUI pour naviguer et exécuter les commandes.
    """
    import asyncio
    from textual.app import App, ComposeResult
    from textual.containers import Vertical, Horizontal
    from textual.widgets import Header, Footer, ListView, ListItem, Static
    from textual.reactive import reactive

    commands = load_commands()


    class CommandCard(Vertical):
        def __init__(self, command_data: dict):
            super().__init__(classes="card")
            self.command_data = command_data
    
            self.title = Static(f"📦 {command_data['title']}", classes="card-title")
            self.cmdline = Static(command_data["command"], classes="card-command")
            self.meta = Static(
                f"[{command_data['category']}]  Tags: {', '.join(command_data['tags'])}",
                classes="card-meta"
            )
        async def on_mount(self):
            self.mount(self.title, self.cmdline, self.meta)

    class CommandItem(ListItem):
        def __init__(self, command_data: dict):
            super().__init__()
            self.command_data = command_data
            self.card = CommandCard(command_data)
    
        async def on_mount(self):
            await self.mount(self.card)

    class CommandTUI(App):
        CSS_PATH = "styles/tui.tcss"
        BINDINGS = [("q", "quit", "Quitter"), ("enter", "run_command", "Exécuter")]

        selected_command = reactive(None)

        def compose(self) -> ComposeResult:
            yield Header()
            self.list_view = ListView(*[CommandItem(cmd) for cmd in commands])
            yield Vertical(self.list_view)
            yield Footer()

        def on_list_view_selected(self, event: ListView.Selected):
            self.selected_command = event.item.command_data

        def action_run_command(self):
            if self.selected_command:
                cmd = self.selected_command
                template = Template(cmd["command"])
                vars_needed = {}

                for var in cmd["variables"]:
                    val = input(f"{var['description']} ({var['name']}): ") or var.get("default", "")
                    vars_needed[var["name"]] = val

                final_cmd = template.render(**vars_needed)
                print(f"\n👉 Commande : {final_cmd}")
                confirm = input("Lancer cette commande ? (y/N): ").lower()
                if confirm == "y":
                    import os
                    os.system(final_cmd)
                    input("\nAppuyez sur Entrée pour revenir...")
                    self.exit()

    CommandTUI().run()



if __name__ == "__main__":
    app()

