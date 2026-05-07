[![Français](https://img.shields.io/badge/🇫🇷%20Français-blue)](/demo/README/README.fr.md)
[![Español](https://img.shields.io/badge/🇪🇸%20Español-yellow)](/demo/README/README.es.md)
[![Português](https://img.shields.io/badge/🇧🇷%20Português-green)](/demo/README/README.pt-br.md)
[![中文](https://img.shields.io/badge/🇨🇳%20中文-red)](/demo/README/README.zh-cn.md)
[![日本語](https://img.shields.io/badge/🇯🇵%20日本語-white)](/demo/README/README.ja.md)
[![한국어](https://img.shields.io/badge/🇰🇷%20한국어-lightgrey)](/demo/README/README.ko.md)

# Lego Web Crawler
**Large-scale e-commerce data extraction and structuring** <br>
A technical case study by Antoine

## Description
This project automates the collection of the [Lego.com](https://www.lego.com) product catalog and transforms it into a structured, queryable SQL database. <br>
It relies on **Playwright** to drive a real browser (JavaScript rendering, Single Page Application) and the **Peewee** ORM for data persistence. The whole pipeline is controllable in real time via an interactive CLI.

![](/demo/assets/data-preview.png?raw=true "Sample collected data")

### Use Cases
 * **Price monitoring** : continuous tracking of prices and promotions
 * **Catalog analysis** : assortment comparison, new product detection
 * **Data enrichment** : feeding price comparison engines or marketing catalogs

### Features
 * **Interactive CLI** : `start`, `pause`, `resume`, `stop`, `restart` and `status` commands to control the crawler without touching the code
 * **Robust scraping** : each field (price, stock, image…) is extracted independently — if one selector changes, the rest of the collection continues uninterrupted
 * **Controlled parallelism** : up to 5 pages scraped simultaneously via an asyncio `Semaphore`, configurable as needed
 * **Auto-resume** : the current page is persisted in the database; the crawler picks up exactly where it left off
 * **Session management** : hot browser context restart (cookies, user-agent) without interrupting the collection

### Tech Stack

| Layer            | Technology               |
|------------------|--------------------------|
| Browser          | Playwright (Chromium)    |
| Persistence      | Peewee ORM + SQLite      |
| Concurrency      | asyncio + Semaphore      |
| Configuration    | PyYAML                   |


## Usage Tutorial

### Installing Dependencies
Once the repository is downloaded (or cloned), make sure you have **Python 3.11+** installed on your machine, then run the following commands to install the required dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configuration
You can configure your preferences in the `config.yml` file. <br>
For example, if you want to see the Chromium browser during execution, set the parameter to: `headless: False`.

### Running the Application
The application provides a simple terminal interface to control the crawler easily. <br>
Simply run the `main.py` file.

![](/demo/assets/main-preview.png?raw=true "Terminal UI")

### Using the Library
If you want to integrate the crawler into another script, you can use the modules in the `src/` folder. <br>
Here is a minimal usage example:

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

Once the data is collected in the database, you can read it easily with the utilities in `utils/data.py`:

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# Available columns: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## Notices & Ethics

This project is an independent technical demonstration. Courtesy delays (`asyncio.sleep`) are built in to limit the load on target servers. <br>
**LEGO®** is a registered trademark of the **LEGO** Group. This project is neither affiliated with nor endorsed by it.
