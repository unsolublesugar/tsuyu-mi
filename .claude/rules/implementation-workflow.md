---
description: 実装ワークフローのルール
globs: *
---

# 実装ワークフロー

## ステップごとの進め方

1. Issue を作成する
2. `feature/issue-XX-description` ブランチを切る
3. 実装する
4. `/update-specs` で仕様書との乖離をチェックし、必要なら更新する
5. コミット・プッシュ → PR 作成
6. マージ後、main に戻って次のステップへ

## Claude Code 関連の作業時

Skill（`.claude/skills/`）、ルール（`.claude/rules/`）、CLAUDE.md、仕様ドキュメントの配置など、Claude Code に関わるファイルを作成・変更する際は、**公式ドキュメントを参照して最新の情報を確認してから作業すること**。

Claude Code の仕様（ファイル配置パス、frontmatter 形式など）は変更される可能性があるため、古い知識で進めない。
