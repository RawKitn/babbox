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

def save_commands(commands):
    with open(DB_PATH, "w") as f:
        json.dump(commands, f, indent=2)

@app.command()
def help():
    """
    Affiche l’aide et la liste des commandes disponibles.
    """
    typer.echo("🧰 Babbox - Outil de stockage et d’exécution de commandes CLI")
    typer.echo("\nCommandes disponibles :\n")
    typer.echo("  add                         Ajouter une nouvelle commande")
    typer.echo("  edit <ID>                   Modifier une commande existante")
    typer.echo("  list                        Lister les commandes enregistrées")
    typer.echo("      --category <CAT>          Listing par catégorie")
    typer.echo("      --tag <TAG>               Listing par tag")
    typer.echo("      --search <KEYWORD>        Listing par mot-clé")
    typer.echo("  run <ID>                    Exécuter une commande")
    typer.echo("  select                      Rechercher une commande via fzf (option --run)")
    typer.echo("  tui                         Interface visuelle (TUI)")
    typer.echo("  help                        Afficher cette aide")

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
def list(
    category: str = typer.Option(None, "--category", "-c", help="Filtrer par catégorie"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filtrer par tag"),
    search: str = typer.Option(None, "--search", "-s", help="Filtrer par mot-clé dans le titre")
):
    """
    Liste les commandes enregistrées avec des filtres optionnels.
    """
    commands = load_commands()
    filtered = []

    for cmd in commands:
        if category and cmd["category"].lower() != category.lower():
            continue
        if tag and tag.lower() not in [t.lower() for t in cmd["tags"]]:
            continue
        if search and search.lower() not in cmd["title"].lower():
            continue
        filtered.append(cmd)

    if not filtered:
        typer.echo("⚠️  Aucune commande trouvée avec ces critères.")
        raise typer.Exit()

    for cmd in filtered:
        typer.echo(f"🔹 [{cmd['id']}] {cmd['title']} ({cmd['category']}) — Tags: {', '.join(cmd['tags'])}")


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
    description = typer.prompt("Description de la commande")
    contexte = typer.prompt("Contexte d'utilisation (ex: maintenance, prod, dev...)")
    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

    variables = []
    has_vars = typer.confirm("La commande utilise-t-elle des variables ?", default=False)
    while has_vars:
        name = typer.prompt("Nom de la variable")
        gendesc = typer.prompt("Description de cette variable")
        default = typer.prompt("Valeur par défaut (laisser vide si aucune)", default="")
        variables.append({
            "name": name,
            "description": gendesc,
            "default": default
        })
        has_vars = typer.confirm("Ajouter une autre variable ?", default=False)

    # Création de l'objet
    now = datetime.utcnow().isoformat() + "Z"
    
    # Récupération du dernier ID numérique
    commands = load_commands()
    existing_ids = [int(cmd["id"]) for cmd in commands if cmd["id"].isdigit()]
    next_id = f"{(max(existing_ids) + 1) if existing_ids else 1:03}"

    # Demande à l'utilisateur s’il souhaite personnaliser l’ID
    use_custom_id = typer.confirm(f"Souhaites-tu définir un ID manuellement ? (sinon {next_id} sera utilisé)", default=False)
    cmd_id = typer.prompt("ID de la commande", default=next_id) if use_custom_id else next_id


    new_command = {
        "id": cmd_id,
        "title": title,
        "command": command,
        "category": category,
        "tags": tags,
        "description": description,
        "contexte": contexte,
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
    import uuid
    from textual.screen import Screen
    from textual.app import App, ComposeResult
    from textual.containers import Vertical, Horizontal
    from textual.widgets import Input, Button, Header, Footer, ListView, ListItem, Static
    from textual.reactive import reactive
    from textual.message import Message
    from datetime import datetime


    commands = load_commands()

    class CommandAdded(Message):
        def __init__(self, command: dict) -> None:
            self.command = command
            super().__init__()

    class CommandAddScreen(Screen):

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static("➕ Nouvelle commande", classes="screen-title")
            yield Input(placeholder="Titre de la commande", id="title")
            yield Input(placeholder="Commande (avec {{ var }})", id="command")
            yield Input(placeholder="Catégorie", id="category")
            yield Input(placeholder="Tags (séparés par des virgules)", id="tags")
            yield Input(placeholder="Description", id="description")
            yield Input(placeholder="Contexte d'utilisation", id="contexte")
            yield Button("➕ Ajouter une variable", id="add_var", variant="default")
            self.var_inputs = []
            yield Vertical(*self.var_inputs, id="variables-container")
            yield Horizontal(
                Button("Valider", id="submit", variant="primary"),
                Button("Annuler", id="cancel", variant="default"),
                classes="button-row"
            )
            yield Footer()

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "submit":
                title = self.query_one("#title", Input).value.strip()
                command = self.query_one("#command", Input).value.strip()
                category = self.query_one("#category", Input).value.strip()
                tags_str = self.query_one("#tags", Input).value.strip()
                description = self.query_one("#description", Input).value.strip()
                contexte = self.query_one("#contexte", Input).value.strip()

                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

                variables = []
                for row in self.var_inputs:
                    name = row.query_one(".var-name", Input).value.strip()
                    var_desc = row.query_one(".var-desc", Input).value.strip()
                    default = row.query_one(".var-default", Input).value.strip()
                    if name:
                        variables.append({
                            "name": name,
                            "description": var_desc,
                            "default": default
                        })

                if not title or not command or not category:
                    return  # Optionnel : message d’erreur

                commands = load_commands()
                next_id = f"{(max([int(c['id']) for c in commands if c['id'].isdigit()] or [0]) + 1):03}"

                new_command = {
                    "id": next_id,
                    "title": title,
                    "command": command,
                    "category": category,
                    "tags": tags,
                    "description": description,
                    "contexte": contexte,
                    "variables": variables,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "updated_at": datetime.utcnow().isoformat() + "Z"
                }

                commands.append(new_command)
                save_commands(commands)

                # On pop l’écran d’ajout
                self.app.post_message(CommandAdded(new_command))

                # Rafraîchir la liste dans l’app principale
                if isinstance(self.app, CommandTUI):
                    self.app.refresh_list()

            elif event.button.id == "add_var":
                container = self.query_one("#variables-container", Vertical)

                var_name = Input(placeholder="Nom", classes="var-name")
                var_desc = Input(placeholder="Description", classes="var-desc")
                var_default = Input(placeholder="Valeur par défaut", classes="var-default")
                row = Horizontal(var_name, var_desc, var_default)
                self.var_inputs.append(row)
                await container.mount(row)  # monte dynamiquement le bloc


            elif event.button.id == "cancel":
                self.app.pop_screen()


    class CommandCard(Vertical):
        def __init__(self, command_data: dict):
            super().__init__(classes="card")
            self.command_data = command_data
    
            self.title = Static(f"📦 {command_data['title']}", classes="card-title")
            self.cmdline = Static(command_data["command"], classes="card-command")
            self.meta = Static(
                f"[{command_data['category']}]  Tags: {', '.join(command_data['tags'])}\n",
                classes="card-meta"
            )
            # Ajout d'un bloc de description des variables
            var_lines = []
            if command_data["variables"]:
                for var in command_data["variables"]:
                    desc = var.get("description", "—")
                    default = var.get("default", "")
                    line = f"- {var['name']} : {desc} (par défaut : {default})"
                    var_lines.append(line)
            else:
                var_lines.append("Aucune variable.")

            self.description_block = Static(
                f"📝 Description : {command_data.get('description', '—')}",
                classes="card-description"
            )

            self.context_block = Static(
                f"📁 Contexte : {command_data.get('contexte', '—')}\n\n",
                classes="card-context"
            )

            self.var_block = Static(
                "🔧 Variables :\n" + "\n".join(var_lines),
                classes="card-variables"
            )

        async def on_mount(self):
            self.mount(self.title, self.cmdline, self.meta, self.description_block, self.context_block, self.var_block)

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

        async def on_command_added(self, message: CommandAdded) -> None:
            # Revenir à l'écran principal et recharger
            await self.pop_screen()
            self.refresh_list()

        def refresh_list(self):
            if not hasattr(self, 'list_view'):
                return  # sécurité
            self.list_view.clear()
            for cmd in load_commands():
                self.list_view.append(CommandItem(cmd))
            self.set_focus(self.list_view)


        def compose(self) -> ComposeResult:
            yield Header()
            self.list_view = ListView(*[CommandItem(cmd) for cmd in commands])
            yield Vertical(self.list_view)
            yield Button("➕ Ajouter une commande", id="add", variant="primary")
            yield Footer()

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "add":
                await self.push_screen(CommandAddScreen())

        async def on_command_added(self, message: CommandAdded) -> None:
            self.refresh_list()
            self.set_focus(self.list_view)
            await self.pop_screen()

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

