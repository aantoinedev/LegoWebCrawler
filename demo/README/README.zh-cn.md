# Lego Web Crawler
**大规模电商数据抓取与结构化处理** <br>
技术案例研究，作者：Antoine

## 项目简介
本项目自动化采集 [Lego.com](https://www.lego.com) 的产品目录，并将其转化为结构化、可查询的 SQL 数据库。<br>
项目使用 **Playwright** 驱动真实浏览器（支持 JavaScript 渲染和单页应用），并采用 **Peewee** ORM 进行数据持久化。整个流程可通过交互式 CLI 实时控制。

![](/demo/assets/data-preview.png?raw=true "采集数据示例")

### 应用场景
 * **价格监控**：持续追踪价格变动与促销活动
 * **目录分析**：品类对比、新品检测
 * **数据增强**：为价格比较平台或营销目录提供数据支持

### 功能特性
 * **交互式 CLI**：支持 `start`、`pause`、`resume`、`stop`、`restart` 和 `status` 命令，无需修改代码即可控制爬虫
 * **健壮的抓取机制**：每个字段（价格、库存、图片等）独立提取 —— 某个选择器失效时，其余字段的采集不受影响
 * **受控并发**：通过 asyncio `Semaphore` 最多同时抓取 5 个页面，并发数可按需配置
 * **自动续爬**：当前页面状态持久化至数据库，爬虫可从中断处精确恢复
 * **会话管理**：热重启浏览器上下文（Cookie、User-Agent），不中断数据采集

### 技术栈

| 层级       | 技术                     |
|------------|--------------------------|
| 浏览器     | Playwright (Chromium)    |
| 持久化     | Peewee ORM + SQLite      |
| 并发       | asyncio + Semaphore      |
| 配置       | PyYAML                   |


## 使用教程

### 安装依赖
下载（或克隆）本仓库后，确保已安装 **Python 3.11+**，然后运行以下命令安装所需依赖：

```bash
pip install -r requirements.txt
playwright install chromium
```

### 配置
您可以在 `config.yml` 文件中配置使用偏好。<br>
例如，若希望在运行过程中显示 Chromium 浏览器界面，请将参数设置为：`headless: False`。

### 启动应用
应用在终端中提供简洁的操作界面，方便控制爬虫。<br>
直接运行 `main.py` 文件即可。

![](/demo/assets/main-preview.png?raw=true "终端界面")

### 作为库使用
如需将爬虫集成到其他脚本中，可使用 `src/` 目录下的模块。<br>
以下是一个最简使用示例：

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

数据采集完成后，可通过 `utils/data.py` 中的工具函数轻松读取：

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# 可用字段：id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## 声明与道德规范

本项目为独立的技术演示项目。程序内置了礼貌延迟（`asyncio.sleep`）以降低对目标服务器的访问压力。<br>
**LEGO®** 是 **乐高集团** 的注册商标。本项目与乐高集团无任何关联，亦未获其授权。
