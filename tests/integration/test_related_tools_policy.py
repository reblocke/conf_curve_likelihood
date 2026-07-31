from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_LINKS = {
    "https://reblocke.github.io/wald-inference-tools/",
    "https://reblocke.github.io/compatibility-curve/",
    "https://reblocke.github.io/conf_curve_likelihood/",
    "https://github.com/reblocke/conf_curve_likelihood",
    "https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.2",
    "https://github.com/reblocke/conf_curve_likelihood/blob/main/docs/PRIVACY.md",
}


class FooterParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._footer_depth = 0
        self.footer_count = 0
        self.footer_links: set[str] = set()
        self.footer_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "footer":
            self.footer_count += 1
            self._footer_depth += 1
            return
        if self._footer_depth and tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.footer_links.add(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "footer":
            self._footer_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._footer_depth:
            self.footer_text.append(data)


def test_readme_has_exact_related_wald_tools_block() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    related_block = readme.split("## Related Wald tools\n", maxsplit=1)[1].split(
        "\n## ", maxsplit=1
    )[0]

    for url in REQUIRED_LINKS:
        assert url in related_block
    assert "wald-inference Core v0.4.2" in related_block
    assert "Privacy" in related_block


def test_required_links_and_privacy_note_are_inside_semantic_footer() -> None:
    parser = FooterParser()
    parser.feed((PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8"))

    footer_text = " ".join(" ".join(parser.footer_text).split())
    assert parser.footer_count == 1
    assert REQUIRED_LINKS <= parser.footer_links
    assert "wald-inference Core v0.4.2" in footer_text
    assert "Privacy:" in footer_text
