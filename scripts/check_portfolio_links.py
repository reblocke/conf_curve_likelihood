from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CATALOG_URL = "https://reblocke.github.io/wald-inference-tools/"
INTEGRATED_URL = "https://reblocke.github.io/conf_curve_likelihood/"
APP_REPOSITORY_URL = "https://github.com/reblocke/conf_curve_likelihood"
CORE_RELEASE_URL = "https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1"
PRIVACY_URL = "https://github.com/reblocke/conf_curve_likelihood/blob/main/docs/PRIVACY.md"
FOCUSED_URLS = (
    "https://reblocke.github.io/compatibility-curve/",
    "https://reblocke.github.io/wald-likelihood-support/",
    "https://reblocke.github.io/critical-effect-size/",
    "https://reblocke.github.io/type-s-m-calibrator/",
    "https://reblocke.github.io/precision-guardrail-planner/",
)
FOOTER_URLS = (
    CATALOG_URL,
    *FOCUSED_URLS,
    INTEGRATED_URL,
    APP_REPOSITORY_URL,
    CORE_RELEASE_URL,
    PRIVACY_URL,
)
LIVE_URLS = FOOTER_URLS
RELATED_TOOLS_HEADING = "## Related Wald tools"
STALE_README_MARKERS = (
    "https://github.com/reblocke/wald-inference-core/releases/tag/v0.1.1",
    "docs/migration/CURRENT_BEHAVIOR.md#privacy-and-data-path",
)


class PortfolioLinkError(RuntimeError):
    """Raised when portfolio navigation is missing, stale, or unavailable."""


class _FooterParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_footer = False
        self.links: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "footer":
            self.in_footer = True
        elif self.in_footer and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "footer":
            self.in_footer = False

    def handle_data(self, data: str) -> None:
        if self.in_footer:
            self.text.append(data)


def validate_portfolio_links(readme: str, html: str) -> list[str]:
    required_readme = (
        CATALOG_URL,
        *FOCUSED_URLS,
        INTEGRATED_URL,
        APP_REPOSITORY_URL,
        CORE_RELEASE_URL,
        "docs/MAINTENANCE.md",
    )
    missing_readme = [value for value in required_readme if value not in readme]
    if readme.count(RELATED_TOOLS_HEADING) != 1:
        missing_readme.append("exactly one Related Wald tools heading")
    stale_readme = [value for value in STALE_README_MARKERS if value in readme]
    if stale_readme:
        raise PortfolioLinkError(
            f"README retains stale portfolio markers: {', '.join(stale_readme)}"
        )
    if missing_readme:
        raise PortfolioLinkError(f"README is missing: {', '.join(missing_readme)}")

    parser = _FooterParser()
    parser.feed(html)
    if parser.links != list(FOOTER_URLS):
        raise PortfolioLinkError(
            "deployed footer links must exactly match the ordered portfolio contract"
        )
    footer_text = " ".join(parser.text)
    if "wald-inference Core v0.4.1" not in footer_text or "privacy" not in footer_text.lower():
        raise PortfolioLinkError("deployed footer must name Core v0.4.1 and its privacy boundary")
    if CATALOG_URL not in html[: html.find("<form")]:
        raise PortfolioLinkError("catalog guidance must be prominent before the input form")
    return [*required_readme, *FOOTER_URLS]


def validate_checked_in_files(root: Path = PROJECT_ROOT) -> list[str]:
    return validate_portfolio_links(
        (root / "README.md").read_text(encoding="utf-8"),
        (root / "web" / "index.html").read_text(encoding="utf-8"),
    )


def _check_live(url: str, attempts: int = 3) -> None:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Cache-Control": "no-cache",
                    "User-Agent": "confcurve-portfolio-link-check/0.2.1",
                },
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise PortfolioLinkError(f"{url} returned HTTP {response.status}")
                response.read(256)
            return
        except (OSError, urllib.error.HTTPError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.5 * (attempt + 1))
    raise PortfolioLinkError(f"could not fetch {url}: {last_error}") from last_error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "also require the catalog, focused apps, integrated site, repository, Core release, "
            "and privacy documentation"
        ),
    )
    args = parser.parse_args()

    checked = validate_checked_in_files()
    print(f"Validated {len(checked)} checked-in portfolio link requirements.")
    if args.live:
        for url in LIVE_URLS:
            _check_live(url)
        print(f"Validated {len(LIVE_URLS)} public portfolio targets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
