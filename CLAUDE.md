# CLAUDE.md

必ず日本語で回答してください。

## Project

Tsuyu-mi — Raindrop.io コレクションの記事を取得・本文抽出・AI 要約し、HTML 一覧を出力するバッチツール。

## Tech Stack

Python 3.11+ / httpx / pydantic / trafilatura / readability-lxml / jinja2 / click / rich

## Commands

- Install: `pip install -e ".[dev]"`
- Run: `python -m src.main run`
- Test: `pytest`
- Lint: `ruff check src/ tests/`

## PR 受け入れ方針

- **`pytest` が全て通らない PR は受け入れない（マージ不可）。** CI ではテストを実行していないため、レビュー時にローカルで `pytest` を実行して確認する。外部からの PR を取り込む際も同様。
- 挙動を変更・修正する PR にはテストを追加する。回帰テスト（例: `tests/unit/test_main_fallback.py`）は削除・骨抜きにしない。
- 詳細は `.claude/rules/git-workflow.md` の「PR 受け入れ基準」を参照。

## References

- 詳細ルール: `.claude/rules/` (自動読み込み)
- アーキテクチャ・設計方針: `.steering/`
- 仕様書: `docs/specs/`
