---
name: update-specs
description: コード変更に関連する docs/specs/ の仕様書を更新する。コード変更の完了時に自動で実行する。
context: fork
---

変更されたファイルに関連する `docs/specs/` 配下の仕様書を特定し、更新案を提示する。

## 手順

1. `git diff --name-only HEAD` で変更されたファイル一覧を取得する（Python ファイル、およびファイルのリネーム・移動・削除を含む）
2. `docs/specs/` 配下の各仕様書を読み込み、変更ファイルのパスや関連モジュール名が含まれるものを特定する。対応表:
   - `src/config.py`, `src/logging_util.py` → `01_overview.md`
   - `src/models.py` → `02_data_models.md`
   - `src/raindrop_client.py` → `03_api_integration.md`
   - `src/content_fetcher.py`, `src/content_extractor.py` → `04_content_extraction.md`
   - `src/summarizer.py`, `prompts/` → `05_summarization.md`
   - `src/html_builder.py`, `docs/` (specs以外) → `06_html_output.md`
   - `src/state_store.py`, `src/article_repository.py` → `07_state_management.md`
   - `src/main.py` → `08_cli_interface.md`
3. 関連する仕様書が見つからない場合、新機能の可能性がある。変更ファイルのパスとディレクトリ構造から機能名を推定し、`docs/specs/` への新規仕様書の作成を提案する
4. 関連する仕様書と変更された Python ファイルの内容を読み込む
5. 仕様書の各セクション（データモデル、フロー、ビジネスルール等）が変更内容と整合しているか確認する
6. 乖離がある場合は、セクションごとに具体的な更新案を提示する
7. ファイルのリネーム・移動・削除があった場合、`git diff --diff-filter=RD --name-status HEAD` で検出し、全仕様書・README.md・CLAUDE.md・`.steering/` 内に旧パスの記載が残っていないか確認する。残っていれば新パスへの更新（または削除済みの旨の反映）を提示する
8. `README.md` を読み込み、変更内容に関連する記載（機能一覧、技術スタック、セットアップ手順等）が最新と合っているか確認する。更新が必要であれば合わせて提示する
9. `CLAUDE.md` を読み込み、変更内容に関連する記載（Tech Stack、Commands 等）が最新と合っているか確認する。更新が必要であれば合わせて提示する
10. `.steering/` 配下のファイル（`architecture.md`, `data-models.md`, `llm-guidelines.md`）を読み込み、変更内容と整合しているか確認する。更新が必要であれば合わせて提示する

## 報告形式

以下の形式で報告する:

- **変更ファイル数**: N件
- **関連する仕様書**: 該当する仕様書のパス一覧（なければ「なし」）
- **更新が必要な箇所**:
  - 仕様書のパス・セクション名・現在の記載・更新案を記載
- **更新不要の場合**: 「仕様書は最新の状態です」と報告
- **新規作成の提案**（関連仕様書が見つからない場合）:
  - 推定した機能名と配置先パス
  - 仕様書の草案
- **パス変更の追従**: リネーム・移動・削除されたファイルの旧パスがドキュメント内に残っていれば、対象ファイルと更新案を記載
- **README.md の更新**: 必要あり/なし（必要な場合は更新案を記載）
- **CLAUDE.md の更新**: 必要あり/なし（必要な場合は更新案を記載）
- **.steering/ の更新**: 必要あり/なし（必要な場合は対象ファイルと更新案を記載）
