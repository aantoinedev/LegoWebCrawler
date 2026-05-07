# Lego Web Crawler
**대규모 이커머스 데이터 수집 및 구조화** <br>
Antoine의 기술 케이스 스터디

## 소개
이 프로젝트는 [Lego.com](https://www.lego.com)의 제품 카탈로그를 자동으로 수집하여 구조화된 SQL 데이터베이스로 변환합니다.<br>
**Playwright**를 사용해 실제 브라우저를 제어하고(JavaScript 렌더링, 싱글 페이지 애플리케이션 지원), **Peewee** ORM으로 데이터를 영속화합니다. 전체 파이프라인은 인터랙티브 CLI를 통해 실시간으로 제어할 수 있습니다.

![](/demo/assets/data-preview.png?raw=true "수집 데이터 예시")

### 활용 사례
 * **가격 모니터링**：가격 및 프로모션 실시간 추적
 * **카탈로그 분석**：상품 구성 비교, 신제품 탐지
 * **데이터 강화**：가격 비교 엔진 또는 마케팅 카탈로그에 데이터 공급

### 주요 기능
 * **인터랙티브 CLI**：코드 수정 없이 `start`, `pause`, `resume`, `stop`, `restart`, `status` 명령어로 크롤러 제어
 * **견고한 스크레이핑**：각 필드(가격, 재고, 이미지 등)를 독립적으로 추출 — 하나의 셀렉터가 변경되어도 나머지 수집은 계속 진행
 * **제어된 병렬 처리**：asyncio `Semaphore`를 통해 최대 5개 페이지를 동시에 스크레이핑 (설정 가능)
 * **자동 재개**：현재 페이지를 DB에 저장하여 중단된 지점부터 정확하게 재개
 * **세션 관리**：수집 중단 없이 브라우저 컨텍스트(쿠키, User-Agent) 핫 리스타트

### 기술 스택

| 계층             | 기술                     |
|------------------|--------------------------|
| 브라우저         | Playwright (Chromium)    |
| 영속성           | Peewee ORM + SQLite      |
| 동시성           | asyncio + Semaphore      |
| 설정             | PyYAML                   |


## 사용 튜토리얼

### 의존성 설치
저장소를 다운로드(또는 클론)한 후, **Python 3.11+**이 설치되어 있는지 확인하고 다음 명령어를 실행하여 필요한 의존성을 설치하세요：

```bash
pip install -r requirements.txt
playwright install chromium
```

### 설정
`config.yml` 파일에서 환경설정을 변경할 수 있습니다.<br>
예를 들어, 실행 중 Chromium 브라우저를 화면에 표시하려면 파라미터를 다음과 같이 설정하세요：`headless: False`.

### 애플리케이션 실행
애플리케이션은 터미널에서 간단한 인터페이스를 제공하여 크롤러를 쉽게 제어할 수 있습니다.<br>
`main.py` 파일을 실행하면 됩니다.

![](/demo/assets/main-preview.png?raw=true "터미널 UI")

### 라이브러리로 사용하기
다른 스크립트에 크롤러를 통합하려면 `src/` 폴더의 모듈을 사용할 수 있습니다.<br>
최소한의 사용 예시는 다음과 같습니다：

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

데이터베이스에 데이터가 수집되면 `utils/data.py`의 유틸리티를 사용하여 간편하게 읽을 수 있습니다：

```py
from utils.data import Data

product = Data('en-us').get_by_id(123456)
print(product.name)

# 사용 가능한 컬럼: id, name, price, theme, sale_infos, rating, pieces, ages, image, logo, url
```

## 고지 사항 및 윤리

이 프로젝트는 독립적인 기술 데모입니다. 대상 서버의 부하를 줄이기 위해 예의상 딜레이(`asyncio.sleep`)가 내장되어 있습니다.<br>
**LEGO®**는 **LEGO 그룹**의 등록 상표입니다. 이 프로젝트는 LEGO 그룹과 무관하며, 공식 승인을 받지 않았습니다.
