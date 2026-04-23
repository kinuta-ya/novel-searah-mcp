# novel-searah-mcp

日本のライトノベル／なろう系小説向け、ビジネス／マーケティング視点の企画支援MCPサーバー。

- 対象市場: 日本（日本語コンテンツのみ）
- 作家・編集者・マーケ担当が、作品企画をフレームワークと市場データで整理するためのMCPツール群を提供
- ユーザーの未公開原稿は外部送信しない

## できること

| 種別 | ツール | 概要 |
|---|---|---|
| 情報取得 | `search_works(query, limit, source)` | 作品をキーワード検索（source = `narou` / `kindle_jp`） |
| 情報取得 | `get_ranking(period, limit, source, category)` | 期間別ランキング（なろうは period 切替、Kindleは現在のベストセラー） |
| メタ | `list_frameworks()` | 利用可能なフレームワークの一覧 |
| 企画 | `build_3c(payload)` | 3C分析（Customer / Competitor / Company） |
| 企画 | `build_stp(payload)` | STP分析（Segmentation / Targeting / Positioning） |
| 企画 | `build_4p(payload)` | 4P分析（Product / Price / Place / Promotion） |
| 企画 | `build_swot(payload)` | SWOT分析＋クロスSWOT |
| 企画 | `build_persona(payload)` | 読者ペルソナシート |

フレームワーク系は LLM 非依存の構造化テンプレート生成です。入力に不足があれば `missing_inputs` と
`follow_up_questions` で「次に何を聞けばよいか」を返すので、クライアント側の LLM が対話で埋めていけます。

## インストール

`uv` がインストールされている前提です（[uv のインストール手順](https://docs.astral.sh/uv/)）。

### 開発版を直接試す

```bash
git clone <this-repo> novel-searah-mcp
cd novel-searah-mcp
uv sync
uv run novel-searah-mcp   # stdio で起動（普段はクライアントから自動起動される）
```

### PyPI 経由（公開後の予定）

```bash
uvx novel-searah-mcp
```

## Claude Desktop に登録する

Claude Desktop の設定ファイルを開きます:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

`mcpServers` に次を追加してください（リポジトリのパスに置き換え）:

```json
{
  "mcpServers": {
    "novel-searah": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/novel-searah-mcp",
        "run",
        "novel-searah-mcp"
      ]
    }
  }
}
```

PyPI 公開後は次のように `uvx` で起動するのがシンプルです:

```json
{
  "mcpServers": {
    "novel-searah": {
      "command": "uvx",
      "args": ["novel-searah-mcp"]
    }
  }
}
```

設定ファイルを保存して Claude Desktop を再起動すると、ツール一覧に上記の8ツールが現れます。

## Claude Code に登録する

```bash
claude mcp add novel-searah -- uv --directory /absolute/path/to/novel-searah-mcp run novel-searah-mcp
```

## 設定（環境変数）

| 変数 | 用途 | デフォルト |
|---|---|---|
| `NOVEL_SEARAH_CACHE_DIR` | キャッシュ格納ディレクトリ | `~/.cache/novel-searah-mcp` |
| `NOVEL_SEARAH_USER_AGENT` | 全HTTP共通の User-Agent | `novel-searah-mcp/<version>` |
| `NOVEL_SEARAH_LOG_LEVEL` | ログレベル | `INFO` |

## 使用例（プロンプト例）

Claude などのクライアントから次のように頼めます:

```
「異世界転生」で検索して、上位5件を3Cの差別化材料に整理して
```

→ 内部で `search_works(query="異世界転生", limit=5)` → `build_3c(...)` が呼ばれ、
競合作品を踏まえた3C分析の下書きが返ります。

```
ペルソナを作りたい。タイトルは「俺TUEEEだけど報われたい」、
ターゲットは社会人男性、職業は会社員、ペインポイントは仕事の徒労感
```

→ `build_persona(...)` が呼ばれ、Demographics / Psychographics / Needs
の構造化シートと未入力項目への追加質問が返ります。

## 制約事項

- **対象市場は日本のみ**（amazon.co.jp、楽天Kobo日本版、なろう日本語作品）
- **Kindle は公開ページ解析のみ**で実装。Amazon の HTML 構造変更で壊れる可能性あり。
  PA-API は使わない（契約不要にするため）
- **本文の自動生成・執筆代行はしない**（クライアント側 LLM の責務）
- **未公開原稿は外部送信しない**（フレームワーク処理はローカル完結）
- アクセスは保守的レート（なろう 1 req/sec、Kindle 0.5 req/sec）。各サイトの利用規約を遵守

## ドキュメント

- 要求・要件定義: [`docs/requirements.md`](./docs/requirements.md)
- 設計書: [`docs/design.md`](./docs/design.md)

## 開発

```bash
uv sync
uv run pytest          # テスト
uv run ruff check      # Lint
uv run mypy src/       # 型チェック
```

新しい情報ソースの追加は `src/novel_searah_mcp/adapters/base.py` の `Adapter` を継承して実装し、
`adapters/__init__.py` と `server.py` の `adapters` dict に登録するだけです。新しいフレームワークも
同様に `frameworks/base.py` の `Framework` を継承して `frameworks/__init__.py` の
`ALL_FRAMEWORKS` に追加します。

## ライセンス

MIT
