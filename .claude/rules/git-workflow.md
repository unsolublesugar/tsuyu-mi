---
description: Git 運用規範（daily-tech-news 準拠）
---

# Git 運用規範

## ブランチ戦略

- Issue 作成 → `feature/issue-XX-description` ブランチ → PR → マージ
- main ブランチへの直接コミットは避ける

## PR ルール

- タイトル: 絵文字 + 概要 + `(#Issue番号)`
  - ✨ 新機能 / 🐛 バグ修正 / 📚 ドキュメント / ⚡ パフォーマンス / ♻️ リファクタ
- 本文冒頭: `Closes #番号`

## ラベル

- `enhancement` (#a2eeef): 新機能
- `bug` (#d73a49): バグ修正
- `documentation` (#0075ca): ドキュメント
- `performance` (#0e8a16): 最適化

## コミットメッセージ

- 日本語または英語で簡潔に
- 変更の「何を」「なぜ」が分かるように
