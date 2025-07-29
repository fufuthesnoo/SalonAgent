"""
Minimal wrapper that lets us run 'computer‑tool' JSON actions.
Supports: navigate, click, type, press, scroll, wait_for_navigation,
download, finish.
"""
from playwright.async_api import async_playwright, TimeoutError
from typing import List, Dict, Any

class ComputerPlaywright:
    def __init__(self):
        self._pw_ctx = None
        self._browser = None

    async def _browser_lazy(self):
        if not self._browser:
            self._pw_ctx = await async_playwright().start()
            self._browser = await self._pw_ctx.chromium.launch(headless=True)
        return self._browser

    async def run(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        browser = await self._browser_lazy()
        page = await browser.new_page()
        result: Dict[str, Any] | None = None

        for act in actions:
            try:
                match act["name"]:
                    case "navigate":
                        # Increase timeout to 60s (60000 ms)
                        await page.goto(act["url"], timeout=60000)
                    case "click":
                        await page.click(act["selector"], timeout=60000)
                    case "type":
                        await page.fill(act["selector"], act["text"], timeout=60000)
                    case "press":
                        await page.press(act["selector"], act.get("key", "Enter"), timeout=60000)
                    case "scroll":
                        await page.evaluate(
                            "window.scrollBy(arguments[0], arguments[1]);",
                            act["x"], act["y"],
                        )
                    case "wait_for_navigation":
                        await page.wait_for_navigation(
                            url=act.get("url_substring") or None,
                            timeout=60000
                        )
                    case "download":
                        async with page.expect_download() as dl_info:
                            await page.click(act["selector"], timeout=60000)
                        dl = await dl_info.value
                        act["download_path"] = await dl.path()
                    case "finish":
                        result = {
                            "reason": act.get("reason"),
                            "answer": act.get("answer"),
                        }
                        break
                    case _:
                        raise ValueError(f"Unknown action: {act['name']}")
            except TimeoutError as e:
                # Return timeout result immediately
                await page.close()
                return {
                    "reason": "timeout",
                    "answer": f"Action '{act['name']}' timed out after 60 seconds: {e.message}"
                }

        await page.close()
        return result or {"status": "ok"}
