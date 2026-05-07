import asyncio
import sys
import os
from src.crawler import Crawler

os.chdir(os.path.dirname(os.path.abspath(__file__)))

##################################################
##                                              ##
##                    CONFIG                    ##
##                                              ##
##################################################

LANG = "en-us"

COMMANDS = {
    "start": "Start the crawler",
    "stop": "Stop the crawler gracefully",
    "pause": "Pause the crawler",
    "resume": "Resume after a pause",
    "restart": "Restart the browser context",
    "status": "Display the current state",
    "help": "Show this help message",
    "exit": "Quit the program",
}

##################################################
##                                              ##
##                 TERMINAL UI                  ##
##                                              ##
##################################################


def log(msg: str, tag: str = "INFO") -> None:
    """
    Prints a colour-coded log line to stdout.

    Args:
        msg (str): Message to display.
        tag (str): Severity label. One of 'INFO', 'OK', 'WARN', 'ERR'. Defaults to 'INFO'.
    """
    tags = {
        "INFO": "\033[94m[INFO]\033[0m",
        "OK": "\033[92m[ OK ]\033[0m",
        "WARN": "\033[93m[WARN]\033[0m",
        "ERR": "\033[91m[ERR ]\033[0m",
    }
    print(f"  {tags.get(tag, tag)}  {msg}")


def print_help() -> None:
    """Prints the list of available commands with their descriptions."""
    print("\n  \033[1mAvailable commands\033[0m")
    print("  " + "─" * 36)
    for cmd, desc in COMMANDS.items():
        print(f"  \033[96m{cmd:<10}\033[0m {desc}")
    print()


def print_banner() -> None:
    """Prints the startup banner, locale info, and the help menu."""
    print()
    print("  \033[1m\033[93m╔══════════════════════════════════╗\033[0m")
    print("  \033[1m\033[93m║        LEGO CRAWLER  v1.0        ║\033[0m")
    print("  \033[1m\033[93m╚══════════════════════════════════╝\033[0m")
    print(f"  Language : {LANG}")
    print_help()


##################################################
##                                              ##
##                     APP                      ##
##                                              ##
##################################################


class App:
    """
    Interactive CLI controller for the Lego crawler.

    Owns a single Crawler instance and exposes each control action as an async method.
    Commands typed in the terminal are dispatched to the matching method via `dispatch()`.
    stdin is read in a thread executor so the asyncio event loop — and therefore the
    crawler — keeps running while waiting for user input.
    """

    def __init__(self):
        self.crawler = Crawler(LANG)
        self.crawler_task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        """Returns True if the crawler task exists and has not yet completed."""
        return self.crawler_task is not None and not self.crawler_task.done()

    async def cmd_start(self) -> None:
        """
        Starts the crawler as a background asyncio task.
        Does nothing if the crawler is already running.
        """
        if self.is_running:
            log("Crawler is already running.", "WARN")
            return
        self.crawler_task = asyncio.create_task(self.crawler.start())
        log("Crawler started.", "OK")

    async def cmd_stop(self) -> None:
        """
        Requests a clean shutdown and waits up to 60 s for the crawler to finish.
        Falls back to task cancellation if the timeout is exceeded.
        Does nothing if the crawler is not running.
        """
        if not self.is_running:
            log("Crawler is not active.", "WARN")
            return
        await self.crawler.stop()
        try:
            await asyncio.wait_for(self.crawler_task, timeout=60)
            log("Crawler stopped gracefully.", "OK")
        except asyncio.TimeoutError:
            self.crawler_task.cancel()
            log("Forced shutdown (timeout).", "WARN")

    async def cmd_pause(self) -> None:
        """
        Pauses the crawler after it finishes processing the current batch.
        Does nothing if the crawler is not running.
        """
        if not self.is_running:
            log("Crawler is not active.", "WARN")
            return
        await self.crawler.pause()
        log("Crawler paused.", "OK")

    async def cmd_resume(self) -> None:
        """
        Resumes the crawler from a paused state.
        Does nothing if the crawler is not currently paused.
        """
        if self.crawler.status != "pause":
            log("Crawler is not paused.", "WARN")
            return
        self.crawler.status = "runing"
        log("Crawler resumed.", "OK")

    async def cmd_restart(self) -> None:
        """
        Triggers a browser context restart without stopping the crawl loop.
        Useful for refreshing cookies or recovering from a stale session.
        Does nothing if the crawler is not running.
        """
        if not self.is_running:
            log("Crawler is not active.", "WARN")
            return
        await self.crawler.restart()
        log("Restarting browser context...", "INFO")

    async def cmd_status(self) -> None:
        """
        Prints the current crawler status, the last completed page index,
        and the number of product URLs queued for scraping.
        """
        status_colors = {
            "off": "\033[90m",
            "initialized": "\033[94m",
            "runing": "\033[92m",
            "pause": "\033[93m",
            "stop": "\033[91m",
        }
        color = status_colors.get(self.crawler.status, "\033[0m")
        page = self.crawler.Page.get()
        print(f"\n  Status      : {color}{self.crawler.status}\033[0m")
        print(f"  Page        : {page}")
        print(f"  Queued URLs : {len(self.crawler.urls)}\n")

    async def cmd_exit(self) -> None:
        """
        Stops the crawler if running, closes the browser, then exits the process.
        Always performs a clean shutdown before calling sys.exit(0).
        """
        if self.is_running:
            log("Stopping crawler before exit...", "INFO")
            await self.cmd_stop()
        await self.crawler.off()
        log("Goodbye!", "OK")
        sys.exit(0)

    async def dispatch(self, cmd: str) -> None:
        """
        Routes a command string to its corresponding handler method.

        Args:
            cmd (str): Command name as typed by the user (already stripped and lowercased).
        """
        actions = {
            "start": self.cmd_start,
            "stop": self.cmd_stop,
            "pause": self.cmd_pause,
            "resume": self.cmd_resume,
            "restart": self.cmd_restart,
            "status": self.cmd_status,
            "help": lambda: (print_help(), None)[1],
            "exit": self.cmd_exit,
        }
        action = actions.get(cmd)
        if action is None:
            log(
                f"Unknown command: '{cmd}'. Type 'help' for the list of commands.",
                "WARN",
            )
            return
        result = action()
        if asyncio.iscoroutine(result):
            await result

    async def run_cli(self) -> None:
        """
        Starts the interactive command loop.

        Reads stdin line by line using run_in_executor so the call never blocks the
        event loop (required on Windows where ProactorEventLoop does not support
        connect_read_pipe on stdin). Each non-empty line is dispatched as a command.
        EOF and KeyboardInterrupt both trigger a clean exit via cmd_exit().
        """
        loop = asyncio.get_event_loop()

        def read_input() -> str:
            sys.stdout.write("  \033[96m>\033[0m ")
            sys.stdout.flush()
            return sys.stdin.readline()

        log("Ready. Type 'start' to begin, 'help' for the command list.", "INFO")
        print()

        while True:
            try:
                line = await loop.run_in_executor(None, read_input)
                cmd = line.strip().lower()
                if cmd:
                    await self.dispatch(cmd)
            except (EOFError, KeyboardInterrupt):
                print()
                await self.cmd_exit()


##################################################
##                                              ##
##                     MAIN                     ##
##                                              ##
##################################################


async def main() -> None:
    """Entry point: prints the banner and starts the CLI loop."""
    print_banner()
    app = App()
    await app.run_cli()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
