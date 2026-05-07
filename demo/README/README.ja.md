# Lego Web Crawler
**大規模なEコマースデータの収集と構造化** <br>
技術的ケーススタディ — Antoine 作

## 概要
このプロジェクトは [Lego.com](https://www.lego.com) の製品カタログを自動収集し、構造化されたクエリ可能なSQLデータベースに変換します。<br>
**Playwright** を使用してリアルブラウザを操作し（JavaScriptレンダリング・シングルページアプリ対応）、**Peewee** ORM でデータを永続化します。全体のパイプラインはインタラクティブな CLI でリアルタイムに制御できます。

![](/demo/assets/data-preview.png?raw=true "収集データのサンプル")

### ユースケース
 * **価格モニタリング**：価格やプロモーションの継続的な追跡
 * **カタログ分析**：品揃えの比較、新製品の検出
 * **データエンリッチメント**：価格比較サイトやマーケティングカタログへのデータ供給

### 機能
 * **インタラクティブ CLI**：`start`、`pause`、`resume`、`stop`、`restart`、`status` コマンドでコードを変更せずにクローラーを制御
 * **堅牢なスクレイピング**：各フィールド（価格、在庫、画像など）を個別に抽出 — セレクターが変更されても残りの収集は継続
 * **制御された並列処理**：asyncio の `Semaphore` により最大5ページを同時スクレイピング（設定可能）
 * **自動再開**：現在のページをDBに保存し、中断した正確な箇所から再開
 * **セッション管理**：収集を中断せずにブラウザコンテキスト（Cookie、User-Agent）をホットリスタート

### 技術スタック

| レイヤー         | 技術                     |
|------------------|--------------------------|
| ブラウザ         | Playwright (Chromium)    |
| 永続化           | Peewee ORM + SQLite      |
| 並行処理         | asyncio + Semaphore      |
| 設定             | PyYAML                   |


## 使用チュートリアル

### 依存関係のインストール
リポジトリをダウンロード（またはクローン）したら、**Python 3.11+** がインストールされていることを確認し、以下のコマンドを実行して必要な依存関係をインストールしてください：

```bash
pip install -r requirements.txt
playwright install chromium
```

### 設定
`config.yml` ファイルで設定を変更できます。<br>
例えば、実行中に Chromium ブラウザを表示したい場合は、パラメータを次のように設定してください：`headless: False`。

### アプリケーションの起動
アプリケーションはターミナルにシンプルなインターフェースを提供し、クローラーを簡単に制御できます。<br>
`main.py` ファイルを実行するだけです。

![](/demo/assets/main-preview.png?raw=true "ターミナル UI")

### ライブラリとして使用する
別のスクリプトにクローラーを統合したい場合は、`src/` フォルダのモジュールを使用できます。<br>
最小限の使用例は以下の通りです：

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

データベースにデータが収集されたら、`utils/data.py` のユーティリティで簡単に読み込めます：

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# 利用可能なカラム: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## 注意事項と倫理

このプロジェクトは独立した技術デモンストレーションです。対象サーバーへの負荷を抑えるため、礼儀的な遅延（`asyncio.sleep`）を組み込んでいます。<br>
**LEGO®** は **LEGOグループ** の登録商標です。このプロジェクトはLEGOグループとは一切関係なく、承認も受けていません。
