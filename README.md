# novel-searah-mcp

日本のライトノベル／なろう系小説向け、ビジネス／マーケティング視点の企画支援MCPサーバー。

- 対象市場: 日本（日本語コンテンツのみ）
- 作家・編集者・マーケ担当が、作品企画をフレームワークと市場データで整理するためのMCPツール群を提供
- ユーザーの未公開原稿は外部送信しない

## ドキュメント

- 要求・要件定義: [`docs/requirements.md`](./docs/requirements.md)
- 設計書: [`docs/design.md`](./docs/design.md)

## 開発状況

現在はプロジェクトスケルトン段階。MVPスコープは `docs/requirements.md` §10 を参照。

## 開発セットアップ

```bash
uv sync
uv run pytest
uv run ruff check
```
