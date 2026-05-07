# Lego Web Crawler :
**Extraction et structuration de données e-commerce à grande échelle** <br>
Projet réalisé par Antoine - Étude de cas technique

## Description
Ce projet automatise la collecte du catalogue produit de [Lego.com](https://www.lego.com) pour le transformer en une base de données SQL structurée et exploitable. <br>
Il repose sur **Playwright** pour piloter un navigateur réel (rendu JavaScript, Single Page Application) et sur l'ORM **Peewee** pour la persistance des données. L'ensemble est pilotable en temps réel via une interface CLI interactive.

![](/demo/assets/data-preview.png?raw=true "Exemple de données collectées")

### Cas d'usage
 * **Veille tarifaire** : suivi des prix et des promotions en continu
 * **Analyse de catalogue** : comparaison d'assortiments, détection de nouveautés
 * **Data enrichment** : alimentation de comparateurs ou de catalogues marketing

### Fonctionnalités
 * **Interface CLI interactive** : commandes `start`, `pause`, `resume`, `stop`, `restart` et `status` pour piloter le crawler sans toucher au code
 * **Scraping robuste** : chaque champ (prix, stock, image…) est extrait de façon isolée : si un sélecteur change, le reste de la collecte continue sans interruption
 * **Parallélisme contrôlé** : jusqu'à 5 pages scraped simultanément via un `Semaphore` asyncio, configurable selon le besoin
 * **Reprise automatique** : la page courante est persistée en base ; le crawler reprend exactement là où il s'est arrêté
 * **Gestion des sessions** : redémarrage du contexte navigateur à chaud (cookies, user-agent) sans interrompre la collecte

### Stack technique

| Couche           | Technologie              |
|------------------|--------------------------|
| Navigateur       | Playwright (Chromium)    |
| Persistance      | Peewee ORM + SQLite      |
| Concurrence      | asyncio + Semaphore      |
| Configuration    | PyYAML                   |


## Tutoriel d'utilisation

### Installation des dépendances
Une fois le dépôt téléchargé (ou cloné), assurez-vous d'avoir **Python 3.11+** installé sur votre machine, puis lancez les commandes suivantes pour installer les dépendances requises :

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configurations
Vous pouvez configurer vos préférences d'utilisation dans le fichier `config.yml`. <br>
Par exemple, si vous souhaitez voir le navigateur Chromium lors de l'exécution du programme, réglez le paramètre sur : `headless: False`.

### Lancement de l'application
L'application propose une interface simple dans le terminal pour piloter le crawler facilement. <br>
Exécutez simplement le fichier `main.py`.

![](/demo/assets/main-preview.png?raw=true "Terminal UI")

### Utilisation de la bibliothèque
Si vous souhaitez intégrer le crawler à un autre script, vous pouvez utiliser les modules du dossier `src/`. <br>
Voici un exemple d'utilisation minimaliste :

```py
from src.crawler import Crawler
import asyncio
import sys

async def main():
    bot = Crawler('en-us')
    await bot.init()
    task = asyncio.create_task(bot.start())
    print("Crawler running!")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input, "Press Enter to stop ")

    print("Stopping, please wait...")
    await bot.stop()

    try:
        await asyncio.wait_for(task, timeout=60)
        print("Crawler stopped gracefully.")
    except asyncio.TimeoutError:
        task.cancel()
        print("Forced shutdown (timeout)")
    finally:
        await bot.off()
        print("Bye bye!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
```

Une fois les données collectées dans la base de données, vous pouvez les lire simplement avec les utilitaires du fichier `utils/data.py` :

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# Available columns: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## Mentions & Éthique

Ce projet est une démonstration technique indépendante. Des délais de courtoisie (`asyncio.sleep`) sont intégrés pour limiter la charge sur les serveurs cibles. <br>
**LEGO®** est une marque déposée du groupe **LEGO**. Ce projet n'est ni affilié, ni approuvé par ce dernier.