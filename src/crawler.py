import asyncio
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from utils import config
from src.scraper import Scraper
from pathlib import Path
from utils.data import Data, Page

PATH = Path(__file__).resolve().parent.parent


class Crawler:
    """
    Orchestrates the full crawl pipeline for lego.com.

    Manages the Playwright browser lifecycle (launch, context, shutdown) and runs
    a continuous loop that fetches product URLs page by page and scrapes each one.
    All scraped data is persisted to a SQLite database via the Data helper.

    Status flow: off -> initialized -> running -> pause / stop / restart / off / reboot.
    Each transition is triggered by the matching method and takes effect after the
    current batch of scrape tasks finishes.

    Args:
        lang (str): Locale string used across all lego.com URLs (e.g. 'fr-fr', 'en-us').
    """

    class Infos:
        """Human-readable descriptions for each possible crawler status."""

        statuses = {
            "off": "Browser is fully closed. Call init() to start fresh.",
            "initialized": "Browser is open and idle. Call start() to begin crawling.",
            "running": "Crawl loop is active — fetching and scraping product pages.",
            "pause": "Crawl loop is suspended. Call resume() to continue.",
            "stop": "Graceful shutdown requested — current batch will finish, then the browser context will be closed.",
            "restart": "Context restart requested — current batch will finish, then a fresh browser context will be created.",
            "reboot": "Full browser reboot in progress — browser and Playwright are being relaunched.",
        }

    def __init__(self, lang: str):
        self.pw = None  # Playwright instance
        self.browser = None  # Chromium browser instance
        self.context = None  # Browser context (holds cookies, user-agent, etc.)
        self.status = "off"
        self.lang = lang or "en-us"
        self._lock = asyncio.Lock()

        self.Data = Data(self.lang)
        self.Page = Page(self.lang)

        self.urls = []

    async def is_running(self):
        return bool(self.status == "running")

    async def init(self):
        """
        Launches the Playwright browser if it is not already open.

        Uses an asyncio Lock to prevent concurrent initialisation calls.
        Automation-detection flags are disabled to reduce the chance of being blocked.
        Sets status to 'initialized' on success.
        """
        async with self._lock:
            if self.browser:
                return
            self.pw = await async_playwright().start()
            self.browser = await self.pw.chromium.launch(
                headless=config.Browser.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            self.status = "initialized"

    async def start(self):
        """
        Starts the main crawl loop.

        Initialises the browser and context if needed, then continuously:
          1. Fetches the list of product URLs for the current page index.
          2. Scrapes all URLs concurrently (bounded by the Scraper's semaphore).
          3. Persists each result to the database (upsert mode).
          4. Advances the page counter and repeats.

        The loop pauses when status is 'pause' (polling every 100 ms) and exits
        when the status changes to anything other than 'running' or 'pause'.

        After the loop, the appropriate teardown is performed based on status:
          - 'restart' : closes the current context and recursively calls start().
          - 'stop'    : closes the context, browser stays open.
          - 'off'     : closes both the browser and the Playwright instance.
        """
        if not self.browser:
            await self.init()
        if not self.context:
            self.context = await self.browser.new_context(user_agent=UserAgent().random)
        scraper = Scraper(self.context, self.lang)
        self.status = "running"

        while await self.is_running():
            if not self.urls:
                self.urls = await scraper.crawl(self.Page.get())

            tasks = [scraper.scrape(url) for url in self.urls]
            for coro in asyncio.as_completed(tasks):
                try:
                    data = await coro
                    if data.get("error"):
                        raise Exception(data.get("error"))
                    self.Data.add_set(**data, force=True)

                except Exception as e:
                    print(f"Error executing the task: {e}")

            self.urls = []
            self.Page.set(self.Page.get() + 1)

            while self.status == "pause":
                await asyncio.sleep(0.1)

        if self.status == "restart":
            await self.context.close()
            self.context = None
            await self.start()

        elif self.status == "stop":
            await self.context.close()
            self.context = None

        elif self.status == "off":
            await self.browser.close()
            await self.pw.stop()

    async def stop(self):
        """
        Requests a graceful shutdown of the crawl loop.

        The current batch of scrape tasks is allowed to complete before the
        browser context is closed. Does nothing if the crawler is not running.
        """
        if await self.is_running():
            self.status = "stop"

    async def pause(self):
        """
        Suspends the crawl loop after the current batch finishes.

        The loop idles in a 100 ms polling interval until the status is changed
        back to 'running' (via resume in App). Does nothing if not running.
        """
        if await self.is_running():
            self.status = "pause"

    async def restart(self):
        """
        Requests a browser context restart.

        After the current batch finishes, the existing context (cookies, session)
        is discarded and a new one is created with a fresh random user-agent.
        The crawl loop then continues from the same page. Does nothing if not running.
        """
        if await self.is_running():
            self.status = "restart"

    async def off(self):
        """
        Shuts down the browser and Playwright completely.

        If the crawler is running, signals the loop to stop and close everything
        once the current batch is done. If the crawler is already idle, closes
        the browser immediately. Sets status to 'off' in all cases.
        """
        if self.browser:
            if await self.is_running():
                self.status = "off"
            else:
                await self.browser.close()
                await self.pw.stop()
                self.status = "off"

    async def reboot(self):
        """
        Performs a full browser reboot: closes the current browser and Playwright
        instance, then launches a new one via init().

        Use this to recover from a crashed or unresponsive browser. Unlike restart(),
        this replaces the entire browser process, not just the context.
        Sets status to 'reboot' during teardown, then 'initialized' after relaunch.
        """
        if self.browser:
            await self.browser.close()
            await self.pw.stop()
            self.status = "reboot"
            await self.init()
