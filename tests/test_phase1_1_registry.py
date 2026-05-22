"""Phase 1.1: registry gate tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.foundation.allowlist import CLOSED_CORPUS_URLS, CORPUS_SIZE
from src.foundation.loader import CONFIG_DIR, DATA_DIR
from src.ingest.registry import RegistryGateError, preflight_registry, run_registry_gate

VALID_ROW = (
    "hdfc-equity-fund-direct-growth,HDFC Equity Fund Direct Growth,"
    "diversified-equity,https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth,"
    "primary,weekly\n"
)
HEADER = "scheme_slug,scheme_name,category,url,priority,refresh_cadence\n"


def _write_registry(path: Path, body: str) -> None:
    path.write_text(HEADER + body, encoding="utf-8")


@pytest.fixture
def registry_dir(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    config = tmp_path / "config"
    config.mkdir()
    # Copy real amc.yaml so registry/amc stay aligned when testing CSV edge cases.
    (config / "amc.yaml").write_text((CONFIG_DIR / "amc.yaml").read_text(encoding="utf-8"))
    return data


def test_preflight_passes_on_project_registry():
    reg = preflight_registry()
    assert len(reg.entries) == CORPUS_SIZE
    assert set(reg.urls) == set(CLOSED_CORPUS_URLS)


def test_run_registry_gate_returns_ingest_registry():
    gate = run_registry_gate(
        registry_path=DATA_DIR / "url_registry.csv",
        amc_path=CONFIG_DIR / "amc.yaml",
    )
    assert gate.ok, gate.errors
    assert gate.registry is not None
    assert len(gate.registry.entries) == 5


def test_rejects_empty_registry(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    _write_registry(reg_path, "")
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert not gate.ok
    assert any("empty" in e.lower() for e in gate.errors)


def test_rejects_four_rows(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    body = "".join(
        [
            "hdfc-mid-cap-fund-direct-growth,HDFC Mid Cap Fund Direct Growth,mid-cap,"
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth,primary,weekly\n",
            VALID_ROW,
            "hdfc-focused-fund-direct-growth,HDFC Focused Fund Direct Growth,focused-equity,"
            "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth,primary,weekly\n",
            "hdfc-large-cap-fund-direct-growth,HDFC Large Cap Fund Direct Growth,large-cap,"
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth,primary,weekly\n",
        ]
    )
    _write_registry(reg_path, body)
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert not gate.ok
    assert any("5" in e for e in gate.errors)


def test_rejects_duplicate_url(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    url = "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
    body = textwrap.dedent(
        f"""\
        hdfc-mid-cap-fund-direct-growth,HDFC Mid Cap,mid-cap,{url},primary,weekly
        hdfc-equity-fund-direct-growth,HDFC Equity,diversified-equity,{url},primary,weekly
        hdfc-focused-fund-direct-growth,HDFC Focused,focused-equity,https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth,primary,weekly
        hdfc-elss-tax-saver-fund-direct-plan-growth,HDFC ELSS,elss,https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth,primary,weekly
        hdfc-large-cap-fund-direct-growth,HDFC Large,large-cap,https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth,primary,weekly
        """
    )
    _write_registry(reg_path, body.replace("\n", "\n") + "\n")
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert not gate.ok
    assert any("duplicate" in e.lower() for e in gate.errors)


def test_rejects_non_allowlist_groww_blog(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    body = textwrap.dedent(
        """\
        hdfc-mid-cap-fund-direct-growth,HDFC Mid Cap,mid-cap,https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth,primary,weekly
        hdfc-equity-fund-direct-growth,HDFC Equity,diversified-equity,https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth,primary,weekly
        hdfc-focused-fund-direct-growth,HDFC Focused,focused-equity,https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth,primary,weekly
        hdfc-elss-tax-saver-fund-direct-plan-growth,HDFC ELSS,elss,https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth,primary,weekly
        hdfc-large-cap-fund-direct-growth,HDFC Large,large-cap,https://groww.in/blog/some-post,primary,weekly
        """
    )
    _write_registry(reg_path, body)
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert not gate.ok


def test_rejects_external_url_in_extra_column(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    # Valid five rows plus a notes column containing hdfcfund.com link (P1-03).
    body = """\
hdfc-mid-cap-fund-direct-growth,HDFC Mid Cap Fund Direct Growth,mid-cap,https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth,primary,weekly,https://www.hdfcfund.com/document.pdf
hdfc-equity-fund-direct-growth,HDFC Equity Fund Direct Growth,diversified-equity,https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth,primary,weekly,
hdfc-focused-fund-direct-growth,HDFC Focused Fund Direct Growth,focused-equity,https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth,primary,weekly,
hdfc-elss-tax-saver-fund-direct-plan-growth,HDFC ELSS Tax Saver Fund Direct Plan Growth,elss,https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth,primary,weekly,
hdfc-large-cap-fund-direct-growth,HDFC Large Cap Fund Direct Growth,large-cap,https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth,primary,weekly,
"""
    reg_path.write_text(
        "scheme_slug,scheme_name,category,url,priority,refresh_cadence,notes\n" + body,
        encoding="utf-8",
    )
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert not gate.ok
    assert any("non-allowlisted" in e for e in gate.errors)


def test_preflight_raises_registry_gate_error(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    _write_registry(reg_path, "")
    with pytest.raises(RegistryGateError) as exc_info:
        preflight_registry(
            registry_path=reg_path,
            amc_path=registry_dir.parent / "config" / "amc.yaml",
        )
    assert exc_info.value.errors


def test_utf8_bom_registry_still_passes(registry_dir: Path):
    reg_path = registry_dir / "url_registry.csv"
    content = (DATA_DIR / "url_registry.csv").read_bytes()
    reg_path.write_bytes(content)  # project file may include BOM handling via utf-8-sig
    gate = run_registry_gate(registry_path=reg_path, amc_path=registry_dir.parent / "config" / "amc.yaml")
    assert gate.ok, gate.errors
