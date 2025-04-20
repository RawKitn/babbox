# Babbox
CLI toolbox made with Python3 &amp; assisted by my friend Chappie :technologist:

## Prerequisites

Primary packages required :

- [ ] Python3
- [ ] fzf

The execution of this code requires some python libraries : 

 - jinja2
 - typer
 - textual

So make sure you have installed these libraries, if not : 

```
pip3 install jinja2 textual textual-dev typer[all]
```

## What can I do with it ?

It offers the possibility to add, edit and execute commands. 

Commands are registered as a noSQL document in a JSON file named **commands.json** and can make use of some variables declared as in a jinja2 template, with `{{ }}`.
Once recorded, you can play these commands by completing variables dynamically or by using their default value.

It also includes TUI (more functionalities in development) to list commands recorded.

## How to use it

The easy way to use it is as below : 

```
python3 cli.py help
```

It will display information about the usage of the script


### Add a new command

To register a new command, use the `add` argument like this : 

```
python3 cli.py add
🆕 Création d'une nouvelle commande
Titre: Redemarrer un service systemd
Commande (avec {{ variable }} si besoin): systemctl restart {{ service }}
Catégorie: system
Tags (séparés par des virgules): systemd,service
La commande utilise-t-elle des variables ? [y/N]: y
Nom de la variable: service
Description de cette variable: Nom du service cible
Valeur par défaut (laisser vide si aucune) []:
Ajouter une autre variable ? [y/N]: N

✅ Commande ajoutée avec l'ID : a39fca27
```

You will be ask to complete the form step-by-step to add the new command into the database.


### Editing registered commands

The scripts include an **edit** function which offers the ability to update a registered command : 

```
python3 cli.py edit 002
📝 Modification de la commande 'Supprimer tous les containers Docker stoppés' (ID: 002)

Titre [Supprimer tous les containers Docker stoppés]:
Commande [docker container prune -f]:
Catégorie [docker]:
Tags (séparés par des virgules) [docker,cleanup,container]:
Souhaites-tu modifier les variables ? [y/N]: y
Ajouter ou modifier une variable ? [y/N]: N
✅ Commande mise à jour avec succès
```


> To see more information for usage, please refer to the **help** to get more information.


## Work in progress 🛠️

- [ ] TUI : Actually, TUI implemented only displays commands in a card-like visualisation ; Later it will offers same actions than in CLI mode.
- [ ] **Delete** function : Not yet implemented
