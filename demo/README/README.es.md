# Lego Web Crawler
**Extracción y estructuración de datos e-commerce a gran escala** <br>
Caso de estudio técnico realizado por Antoine

## Descripción
Este proyecto automatiza la recopilación del catálogo de productos de [Lego.com](https://www.lego.com) para transformarlo en una base de datos SQL estructurada y consultable. <br>
Se apoya en **Playwright** para controlar un navegador real (renderizado JavaScript, Single Page Application) y en el ORM **Peewee** para la persistencia de datos. Todo el pipeline es controlable en tiempo real a través de una interfaz CLI interactiva.

![](/demo/assets/data-preview.png?raw=true "Ejemplo de datos recopilados")

### Casos de uso
 * **Seguimiento de precios** : monitoreo continuo de precios y promociones
 * **Análisis de catálogo** : comparación de surtidos, detección de novedades
 * **Enriquecimiento de datos** : alimentación de comparadores de precios o catálogos de marketing

### Funcionalidades
 * **CLI interactiva** : comandos `start`, `pause`, `resume`, `stop`, `restart` y `status` para controlar el crawler sin tocar el código
 * **Scraping robusto** : cada campo (precio, stock, imagen…) se extrae de forma aislada — si un selector cambia, el resto de la recopilación continúa sin interrupciones
 * **Paralelismo controlado** : hasta 5 páginas scrapeadas simultáneamente mediante un `Semaphore` de asyncio, configurable según necesidad
 * **Reanudación automática** : la página actual se persiste en la base de datos; el crawler retoma exactamente donde lo dejó
 * **Gestión de sesiones** : reinicio en caliente del contexto del navegador (cookies, user-agent) sin interrumpir la recopilación

### Stack técnico

| Capa             | Tecnología               |
|------------------|--------------------------|
| Navegador        | Playwright (Chromium)    |
| Persistencia     | Peewee ORM + SQLite      |
| Concurrencia     | asyncio + Semaphore      |
| Configuración    | PyYAML                   |


## Tutorial de uso

### Instalación de dependencias
Una vez descargado (o clonado) el repositorio, asegúrese de tener **Python 3.11+** instalado en su máquina y ejecute los siguientes comandos para instalar las dependencias necesarias:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configuración
Puede configurar sus preferencias en el archivo `config.yml`. <br>
Por ejemplo, si desea ver el navegador Chromium durante la ejecución, establezca el parámetro: `headless: False`.

### Lanzamiento de la aplicación
La aplicación ofrece una interfaz sencilla en el terminal para controlar el crawler fácilmente. <br>
Simplemente ejecute el archivo `main.py`.

![](/demo/assets/main-preview.png?raw=true "Terminal UI")

### Uso de la biblioteca
Si desea integrar el crawler en otro script, puede usar los módulos de la carpeta `src/`. <br>
Aquí tiene un ejemplo de uso mínimo:

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

Una vez recopilados los datos en la base de datos, puede leerlos fácilmente con las utilidades de `utils/data.py`:

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# Columnas disponibles: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## Avisos y ética

Este proyecto es una demostración técnica independiente. Se han integrado retardos de cortesía (`asyncio.sleep`) para limitar la carga en los servidores objetivo. <br>
**LEGO®** es una marca registrada del grupo **LEGO**. Este proyecto no está afiliado ni aprobado por dicho grupo.
