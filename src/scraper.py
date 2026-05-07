import asyncio
from playwright.async_api import BrowserContext, Page, Locator
import unicodedata
from utils.data import Page
import random


class Scraper:
    """
    Handles all page-level scraping and crawling operations for lego.com.

    This class provides three main entry points:
    - `scrape(url)`  : scrape a single product page from its URL.
    - `search(query)`: search for a product by name or set ID, then scrape the first result.
    - `crawl(page_index)`: collect all product URLs listed on a category page.

    Concurrent requests are controlled by an asyncio Semaphore (default: 5 simultaneous pages).

    Args:
        context (BrowserContext): An active Playwright browser context to open pages from.
        lang (str): Locale string used in lego.com URLs (e.g. 'fr-fr', 'en-us').
        limit (int | None): Maximum number of pages that can be scraped concurrently. Defaults to 5.
    """

    def __init__(self, context: BrowserContext, lang: str, limit: int | None = 5):
        self.context = context
        self.lang = lang or "en-us"
        self.semaphore = asyncio.Semaphore(limit)
        self.Page = Page(self.lang)

    async def _scrape(self, page: Page) -> dict:
        """
        Core scraping logic: extracts all product metadata from an already-loaded page.

        This internal method assumes the page is already navigated to a product URL.
        It defines locators for every target field, waits for them concurrently, then
        extracts and normalises each value. Call `scrape()` or `search()` instead of
        this method unless you already hold an open Page object.

        Args:
            page (Page): An active Playwright Page instance pointed at a lego.com product URL.

        Returns:
            dict: A dictionary with the following keys:
                - 'id'         (str)  : Set number, e.g. '75192'.
                - 'name'       (str)  : Full product name.
                - 'price'      (str)  : Displayed price, e.g. '€449.99', or 'Not for sale'.
                - 'theme'      (str)  : Theme slug extracted from the breadcrumb link, e.g. 'star-wars'.
                - 'sale_infos' (str)  : Stock status, e.g. 'Available now' or 'Retired product'.
                - 'rating'     (float): Average customer rating (0.0-5.0), or -1 if absent.
                - 'pieces'     (int)  : Total piece count, or -1 if absent.
                - 'ages'       (str)  : Recommended age range, e.g. '18+'.
                - 'image'      (str)  : High-resolution product image URL (1200x1200).
                - 'logo'       (str)  : Theme logo image URL (query string stripped).
                - 'url'        (str)  : Source URL of the scraped page.

            On failure, returns: {'error': '<reason>'}
        """
        try:

            class Locators:
                id = page.locator('[data-test="item-value"]').first
                name = page.locator('[data-test="product-overview-name"]').first
                price = page.locator('[data-test="product-price-display-price"]').first
                theme = page.locator('[data-test="product-overview-div"] a').first
                sale_infos = page.locator(
                    '[data-test="product-overview-availability"]'
                ).first
                rating = page.locator('span:has-text("Average rating ")').first
                pieces = page.locator('[data-test="pieces"] div').first
                ages = page.locator('[data-test="ages"] div').first
                image = page.locator(
                    '[data-test="mediagallery-image-button-0"] img'
                ).first
                logo = page.locator('[data-test="product-attributes"] img').first

            class SafeGet:
                """
                Wraps a Playwright Locator to make every extraction non-throwing.

                Each method silently returns an empty string on timeout or any error,
                so a single missing element never aborts the whole scrape.
                """

                def __init__(self, locator: Locator):
                    self.locator = locator

                async def text(self) -> str:
                    """Returns the raw text content of the element, or '' on failure."""
                    try:
                        return (await self.locator.text_content(timeout=1000)) or ""
                    except:
                        return ""

                async def inner(self) -> str:
                    """Returns the visible inner text of the element, or '' on failure."""
                    try:
                        return (await self.locator.inner_text(timeout=1000)) or ""
                    except:
                        return ""

                async def attr(self, attr: str) -> str:
                    """Returns the value of the given HTML attribute, or '' on failure."""
                    try:
                        return (
                            await self.locator.get_attribute(attr, timeout=1000)
                        ) or ""
                    except:
                        return ""

                async def eval(self, expression: str) -> str:
                    """Evaluates a JS expression on the element and returns the result, or '' on failure."""
                    try:
                        return (
                            await self.locator.evaluate(expression, timeout=1000)
                        ) or ""
                    except:
                        return ""

            # Wait for all elements concurrently; individual failures are collected, not raised.
            await asyncio.gather(
                Locators.id.wait_for(state="attached", timeout=5000),
                Locators.name.wait_for(state="visible", timeout=5000),
                Locators.price.wait_for(state="visible", timeout=5000),
                Locators.theme.wait_for(state="attached", timeout=5000),
                Locators.sale_infos.wait_for(state="visible", timeout=5000),
                Locators.rating.wait_for(state="attached", timeout=3000),
                Locators.pieces.wait_for(state="visible", timeout=5000),
                Locators.ages.wait_for(state="visible", timeout=5000),
                Locators.image.wait_for(state="visible", timeout=5000),
                Locators.logo.wait_for(state="visible", timeout=5000),
                return_exceptions=True,
            )

            id: str = await SafeGet(Locators.id).text()
            name: str = await SafeGet(Locators.name).inner()
            price: str = await SafeGet(Locators.price).inner()
            theme: str = await SafeGet(Locators.theme).attr("href")
            sale_infos: str = await SafeGet(Locators.sale_infos).inner()
            rating: str = await SafeGet(Locators.rating).text()
            pieces: str = await SafeGet(Locators.pieces).inner()
            ages: str = await SafeGet(Locators.ages).inner()
            image: str = await SafeGet(Locators.image).attr("src")
            logo: str = await SafeGet(Locators.logo).eval(
                "node => node.currentSrc || node.closest('picture').querySelector('source').srcset.split(' ')[0]"
            )

            if not all([id, name]):
                raise ValueError("Incomplete data detected")

            return {
                "id": id.strip().replace("#", ""),
                "name": name.strip(),
                "price": (
                    unicodedata.normalize("NFKD", price.strip())
                    if price
                    else "Not for sale"
                ),
                "theme": (
                    theme.strip()
                    .replace(f"/{self.lang}/themes/", "")
                    .replace(f"/{self.lang}/", "")
                    if theme
                    else "Theme not found"
                ),
                "sale_infos": (
                    unicodedata.normalize("NFKD", sale_infos.strip())
                    if sale_infos
                    else "Sale Infos not found"
                ),
                "rating": (
                    float(
                        rating.strip()
                        .replace("Average rating ", "")
                        .replace(" out of 5 stars", "")
                    )
                    if rating
                    else -1
                ),
                "pieces": int(pieces.strip()) if pieces else -1,
                "ages": ages.strip() if ages else "Ages not found",
                "image": (
                    image.replace("fit=crop", "fit=bounds")
                    .replace("width=800", "width=1200")
                    .replace("height=800", "height=1200")
                    if image
                    else "Image not found"
                ),
                "logo": logo.split("?")[0] if logo else "Logo not found",
                "url": page.url,
            }

        except Exception as e:
            return {"error": f"Scrape failed: {str(e)}"}

    async def scrape(self, url: str):
        """
        Opens a new browser page, navigates to the given product URL and scrapes it.

        Acquires one semaphore slot for the duration of the operation to cap concurrency.
        A random delay (3-6 s) is added after page load to mimic human browsing behaviour.

        Args:
            url (str): Full lego.com product URL to scrape.

        Returns:
            dict: Scraped product data (see `_scrape` for the full schema),
                  or {'error': '<reason>'} on failure.
        """

        async with self.semaphore:
            page = await self.context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(random.uniform(3, 6))
                return await self._scrape(page)

            except Exception as e:
                return {"error": f"Semaphor scrape faild: {e}"}
            finally:
                await page.close()

    async def search(self, query: str):
        """
        Searches lego.com for a product and scrapes the first matching result.

        If `query` is a numeric set ID, the method dismisses age-gate and cookie banners,
        then checks whether the search redirected directly to a product page. Otherwise it
        waits for the product grid, collects all result URLs, and scrapes the first one.

        Args:
            query (str): A free-text product name (e.g. 'Millennium Falcon') or a
                         numeric set ID (e.g. '75192').

        Returns:
            dict: Scraped product data (see `_scrape` for the full schema),
                  or {'error': '<reason>'} if the search or scrape fails.
        """
        async with self.semaphore:
            page = await self.context.new_page()

            try:
                await page.goto(
                    f"https://www.lego.com/{self.lang}/search?q={query.replace(' ', '+')}",
                    wait_until="networkidle",
                    timeout=10000,
                )

                if query.isdigit():
                    try:
                        await page.locator('[data-test="age-gate-grown-up-cta"]').click(
                            timeout=3000
                        )
                    except:
                        pass
                    try:
                        await page.locator(
                            '[data-test="cookie-necessary-button"]'
                        ).click(timeout=3000)
                    except:
                        pass

                    if "/product/" in page.url:
                        return await self._scrape(page)

                grid = page.locator('[data-test="product-listing"]').first
                await grid.wait_for(state="visible", timeout=10000)

                items = await page.locator('article[data-test="product-leaf"]').all()

                if not items:
                    raise ValueError(f"No results found for the query: {query}")

                urls = [
                    f"https://www.lego.com{await i.locator('a').first.get_attribute('href')}"
                    for i in items
                ]

                await page.goto(
                    str(urls[0]), wait_until="domcontentloaded", timeout=10000
                )
                return await self._scrape(page)

            except Exception as e:
                return {"error": f"Search failed: {str(e)}"}
            finally:
                await page.close()

    async def crawl(self, page_index: int) -> list:
        """
        Collects all product URLs listed on a given page of the 'all-sets' category.

        Navigates to the paginated category listing and extracts the href of the first
        anchor inside each product card. If the grid never appears (e.g. last page
        reached), the page counter is reset to 1 and an empty list is returned.

        Args:
            page_index (int): 1-based page number to fetch from the category listing.

        Returns:
            list[str]: A list of absolute product URLs found on the page.
                       Returns an empty list if the page has no results or on error.
        """
        page = await self.context.new_page()
        try:
            await page.goto(
                f"https://www.lego.com/{self.lang}/categories/all-sets?page={page_index}&offset=0",
                wait_until="networkidle",
                timeout=10000,
            )

            grid = page.locator('[data-test="product-listing"]').first

            try:
                await grid.wait_for(state="visible", timeout=10000)
            except:
                self.Page.set(1)
                return []

            items = await page.locator('article[data-test="product-leaf"]').all()

            if not items:
                raise ValueError(f"No results found")

            urls = [
                f"https://www.lego.com{await i.locator('a').first.get_attribute('href')}"
                for i in items
            ]
            return urls

        except Exception as e:
            print(f"Crawl failed: {str(e)}")
            return []
        finally:
            await page.close()
