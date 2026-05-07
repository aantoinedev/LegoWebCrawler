# Lego Web Crawler
**Extração e estruturação de dados de e-commerce em larga escala** <br>
Um estudo de caso técnico realizado por Antoine

## Descrição
Este projeto automatiza a coleta do catálogo de produtos do [Lego.com](https://www.lego.com) e o transforma em um banco de dados SQL estruturado e consultável. <br>
Ele utiliza o **Playwright** para controlar um navegador real (renderização JavaScript, Single Page Application) e o ORM **Peewee** para a persistência dos dados. Todo o pipeline pode ser controlado em tempo real por meio de uma CLI interativa.

![](/demo/assets/data-preview.png?raw=true "Exemplo de dados coletados")

### Casos de uso
 * **Monitoramento de preços** : acompanhamento contínuo de preços e promoções
 * **Análise de catálogo** : comparação de sortimentos, detecção de novidades
 * **Enriquecimento de dados** : alimentação de comparadores de preços ou catálogos de marketing

### Funcionalidades
 * **CLI interativa** : comandos `start`, `pause`, `resume`, `stop`, `restart` e `status` para controlar o crawler sem alterar o código
 * **Scraping robusto** : cada campo (preço, estoque, imagem…) é extraído de forma isolada — se um seletor mudar, o restante da coleta continua sem interrupções
 * **Paralelismo controlado** : até 5 páginas coletadas simultaneamente via `Semaphore` do asyncio, configurável conforme necessidade
 * **Retomada automática** : a página atual é persistida no banco de dados; o crawler retoma exatamente de onde parou
 * **Gerenciamento de sessões** : reinicialização a quente do contexto do navegador (cookies, user-agent) sem interromper a coleta

### Stack técnica

| Camada           | Tecnologia               |
|------------------|--------------------------|
| Navegador        | Playwright (Chromium)    |
| Persistência     | Peewee ORM + SQLite      |
| Concorrência     | asyncio + Semaphore      |
| Configuração     | PyYAML                   |


## Tutorial de uso

### Instalação das dependências
Após baixar (ou clonar) o repositório, certifique-se de ter o **Python 3.11+** instalado e execute os seguintes comandos para instalar as dependências necessárias:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configuração
Você pode configurar suas preferências no arquivo `config.yml`. <br>
Por exemplo, se quiser visualizar o navegador Chromium durante a execução, defina o parâmetro: `headless: False`.

### Executando a aplicação
A aplicação oferece uma interface simples no terminal para controlar o crawler facilmente. <br>
Basta executar o arquivo `main.py`.

![](/demo/assets/main-preview.png?raw=true "Terminal UI")

### Usando a biblioteca
Se quiser integrar o crawler em outro script, você pode usar os módulos da pasta `src/`. <br>
Aqui está um exemplo mínimo de uso:

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

Após a coleta dos dados no banco de dados, você pode lê-los facilmente com os utilitários de `utils/data.py`:

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# Colunas disponíveis: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## Avisos e ética

Este projeto é uma demonstração técnica independente. Atrasos de cortesia (`asyncio.sleep`) foram integrados para limitar a carga nos servidores de destino. <br>
**LEGO®** é uma marca registrada do grupo **LEGO**. Este projeto não é afiliado nem aprovado por ele.
