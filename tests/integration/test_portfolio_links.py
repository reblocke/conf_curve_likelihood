from __future__ import annotations

import pytest

from check_portfolio_links import (
    CATALOG_URL,
    FOOTER_URLS,
    LIVE_URLS,
    PROJECT_ROOT,
    PortfolioLinkError,
    validate_checked_in_files,
    validate_portfolio_links,
)


def test_checked_in_portfolio_navigation_is_exact() -> None:
    checked = validate_checked_in_files()
    assert CATALOG_URL in checked
    assert set(FOOTER_URLS) <= set(checked)
    assert LIVE_URLS == FOOTER_URLS


def test_missing_readme_catalog_link_is_rejected() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8").replace(CATALOG_URL, "")
    html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    with pytest.raises(PortfolioLinkError, match="README is missing"):
        validate_portfolio_links(readme, html)


def test_reordered_or_missing_footer_link_is_rejected() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    html = (
        (PROJECT_ROOT / "web" / "index.html")
        .read_text(encoding="utf-8")
        .replace(FOOTER_URLS[1], "https://example.test/stale-adjacent/")
    )
    with pytest.raises(PortfolioLinkError, match="ordered portfolio contract"):
        validate_portfolio_links(readme, html)
