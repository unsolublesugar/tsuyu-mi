---
description: Python コーディング規約
globs: "src/**/*.py,tests/**/*.py"
---

# コーディング規約

## スタイル

- Python 3.11+ の機能を活用（type union `X | Y`、`match` 文など）
- ruff でリント（line-length=100）
- 型ヒントを付ける（Pydantic モデルは必須、ユーティリティ関数も推奨）

## エラーハンドリング

- 記事単位で try-except + 続行（1 記事の失敗でパイプライン全体を止めない）
- 失敗理由を state に記録し、次回再試行可能にする
- ログは `logging_util.py` のロガーを使う

## モジュール構成

- `src/models.py` が全モジュール共通の型定義層
- 依存の方向は上位（main.py）→ 下位（utils/）。循環依存禁止
- LLM プロバイダーは Protocol + Factory パターンで抽象化
