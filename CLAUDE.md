# CLAUDE.md

必ず日本語で回答してください。

## Project

Raindrop Collection Summarizer — Raindrop.io コレクションの記事を取得・本文抽出・AI 要約し、HTML 一覧を出力するバッチツール。

## Tech Stack

Python 3.11+ / httpx / pydantic / trafilatura / readability-lxml / jinja2 / click / rich

## Commands

- Install: `pip install -e ".[dev]"`
- Run: `python -m src.main run`
- Test: `pytest`
- Lint: `ruff check src/ tests/`

## References

- 詳細ルール: `.claude/rules/` (自動読み込み)
- アーキテクチャ・設計方針: `.steering/`
- 仕様書: `docs/specs/`
