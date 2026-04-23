# novel-searah-mcp 設計書

> ステータス: **ドラフト v0.2**（2026-04-23 更新）
> 関連: [`requirements.md`](./requirements.md)
> 本書は要件定義と対になる設計ドキュメント。基底クラス・I/F・横断的な設計方針を記述する。

---

## 1. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                  MCPクライアント                     │
│           （Claude Desktop, Claude Code 等）         │
└────────────────────────┬────────────────────────────┘
                         │ stdio (JSON-RPC)
┌────────────────────────▼────────────────────────────┐
│                    server.py                         │
│            （MCPエントリポイント・ツール登録）        │
└──────┬───────────────────────┬──────────────────────┘
       │                       │
┌──────▼──────────┐    ┌───────▼──────────────┐
│  tools/          │    │  frameworks/          │
│  - search        │    │  - base.Framework     │
│  - trends        │    │  - 3c, stp, 4p, swot, │
│  - frameworks    │    │    persona, ...       │
└──────┬──────────┘    └───────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                    adapters/                         │
│   base.Adapter ← narou / kindle_jp / kobo_jp / ...  │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────┐
│   cache.py       │  （diskcache / SQLite, TTL管理）
└─────────────────┘
```

### レイヤの責務

| レイヤ | 責務 | 依存 |
|---|---|---|
| `server` | MCPプロトコル対応、ツール登録、エラーハンドリング | tools, frameworks, adapters |
| `tools` | MCPツールの薄いラッパー、入出力バリデーション | frameworks, adapters, cache |
| `frameworks` | ビジネスフレームワーク変換ロジック | models |
| `adapters` | 外部ソースとの通信・スキーマ変換 | cache, httpx |
| `models` | 共通データ型（pydantic） | — |
| `cache` | 取得結果の永続キャッシュ | — |
| `config` | 環境変数読み込み・設定値の集約 | — |

---

## 2. 共通データモデル（`models.py`）

pydantic v2 で定義。MCP経由ではJSONで受け渡す。

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Literal, Optional

SourceName = Literal[
    "narou", "kindle_jp", "kobo_jp", "booklive", "kakuyomu",
    "alphapolis", "publishers", "google_trends", "bookwalker",
    "novelup", "twitter",
]

class Metrics(BaseModel):
    """作品の指標。ソースにより取れるものが異なるため全てOptional。"""
    bookmarks: Optional[int] = None      # なろう ブクマ
    points: Optional[int] = None         # なろう ポイント
    reviews: Optional[int] = None        # Kindle/Kobo レビュー数
    rating: Optional[float] = None       # Kindle/Kobo 評価
    rank: Optional[int] = None           # 総合順位
    sales_rank: Optional[int] = None     # 電子書籍売上ランク
    word_count: Optional[int] = None     # 総文字数

class Work(BaseModel):
    """全ソース共通の作品表現。"""
    source: SourceName
    source_id: str                       # ソース内での一意ID
    title: str
    author: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    synopsis: Optional[str] = None       # あらすじ（著作権配慮で要約のみ）
    genre: Optional[str] = None
    url: Optional[HttpUrl] = None
    metrics: Metrics = Field(default_factory=Metrics)
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw: dict = Field(default_factory=dict, exclude=True)  # 元レスポンス（内部用）

class HealthStatus(BaseModel):
    name: str
    ok: bool
    latency_ms: Optional[float] = None
    message: Optional[str] = None
```

---

## 3. Adapter 基底クラス（`adapters/base.py`）

### 3.1 責務

- 外部ソースへの HTTP 通信（`httpx.AsyncClient`）
- レート制限（トークンバケット／最小インターバル）
- キャッシュ透過（`cache` レイヤを通す）
- ソース固有のレスポンス → `Work` への変換
- エラーを共通例外に正規化

### 3.2 インターフェース

```python
from abc import ABC, abstractmethod
from typing import Optional
import httpx
from ..models import Work, HealthStatus, SourceName
from ..cache import Cache

class AdapterError(Exception):
    """アダプター共通例外。"""

class RateLimitedError(AdapterError): ...
class NotFoundError(AdapterError): ...
class SourceUnavailableError(AdapterError): ...

class Adapter(ABC):
    name: SourceName
    default_ttl: int = 3600  # キャッシュTTL（秒）。子クラスで上書き可

    def __init__(self, client: httpx.AsyncClient, cache: Cache, *, rps: float = 1.0):
        self.client = client
        self.cache = cache
        self._min_interval = 1.0 / rps

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[Work]:
        """キーワード検索。"""

    @abstractmethod
    async def ranking(
        self, category: Optional[str] = None, period: str = "daily", limit: int = 20
    ) -> list[Work]:
        """ランキング取得。period: daily/weekly/monthly/quarterly/yearly/all."""

    @abstractmethod
    async def detail(self, source_id: str) -> Work:
        """作品詳細。"""

    async def health(self) -> HealthStatus:
        """疎通確認。デフォルトは `search("test", 1)` を呼ぶ。子で上書き可。"""

    # --- 共通ユーティリティ -----------------------------------------
    async def _cached_get(self, url: str, *, ttl: Optional[int] = None, **kwargs) -> dict:
        """キャッシュ透過のGET。キー = url + sorted(params)."""

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """HTTPステータスを共通例外に変換。"""
```

### 3.3 レート制限デフォルト

保守的な値を基準にし、必要に応じて個別に引き上げる。

| ソース | rps（req/sec） | 備考 |
|---|---|---|
| narou | **1.0** | なろう小説APIの運用ガイドに準拠。連続大量取得はしない |
| kindle_jp | 0.5 | 公開ページ解析のみ。アクセス過多回避 |
| kobo_jp | 0.5 | 同上 |
| booklive | 0.5 | 同上 |
| その他Web | 0.5 | デフォルト保守値 |
| google_trends | pytrends 既定 | 429対策でキャッシュ併用 |

### 3.4 アダプター固有の責務分担

| 責務 | Adapter基底 | 個別Adapter |
|---|:---:|:---:|
| レート制限 | ○ | （値の指定のみ） |
| キャッシュ読み書き | ○ | （TTLの指定のみ） |
| HTTPクライアント管理 | ○ | |
| 例外正規化 | ○ | （個別ステータスの判定） |
| スキーマ変換（→Work）| | ○ |
| エンドポイント・クエリ構築 | | ○ |
| User-Agent / 認証 | | ○ |

---

## 4. Framework 基底クラス（`frameworks/base.py`）

### 4.1 責務

- **LLMを呼ばない**。フレームワークは「入力の型変換・構造化・テンプレ適用」に徹し、思考はクライアント側LLMに委ねる
- 入力スキーマ・出力スキーマを宣言
- 情報が不足している場合、追加質問リストを返す
- 構造化データ（JSON）と Markdownレポートの2形態を返す

### 4.2 インターフェース

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import ClassVar

class FrameworkInput(BaseModel):
    """全フレームワーク共通の最小入力。個別フレームワークは継承して追加フィールド定義。"""
    title: str                           # 作品タイトル（仮題OK）
    genre: Optional[str] = None          # 例: "異世界転生", "現代ファンタジー"
    logline: Optional[str] = None        # 一行あらすじ
    target_reader: Optional[str] = None  # 想定読者像（自由記述）
    extra: dict = Field(default_factory=dict)  # 個別フレームワーク用の自由欄

class FrameworkOutput(BaseModel):
    framework: str                       # フレームワーク識別子
    data: dict                           # 構造化データ
    markdown: str                        # 人間可読レポート
    missing_inputs: list[str] = []       # 不足入力があればキーで返す
    follow_up_questions: list[str] = []  # LLMがユーザーに聞くべき追加質問

class Framework(ABC):
    name: ClassVar[str]                  # "3c", "stp", ...
    display_name: ClassVar[str]          # "3C分析", ...
    description: ClassVar[str]           # 1行説明
    InputModel: ClassVar[type[FrameworkInput]] = FrameworkInput

    @abstractmethod
    def build(self, payload: FrameworkInput) -> FrameworkOutput:
        """フレームワーク出力を構築。LLM呼び出しは行わない。"""

    def render_markdown(self, data: dict) -> str:
        """JSON → Markdown 変換。デフォルト実装あり、子で上書き可。"""
```

### 4.3 Markdownスタイル規約

レポート出力のMarkdownは企画書にそのまま貼り付けられる体裁で統一する。

- **絵文字・装飾記号は使用しない**（見出しや箇条書きのみ）
- 見出しは `##` から始める（埋め込み時に階層を調整しやすい）
- 箇条書きは `-` を使用
- 表はGitHub-flavored Markdown
- フレームワーク名は日本語表記（例: 「3C分析」「ペルソナ」）を見出しに使用
- 不足入力がある場合、末尾に「## 追加質問」セクションで提示

### 4.4 MVP対象フレームワーク（5つ）

| name | display_name | 追加入力の例 |
|---|---|---|
| `3c` | 3C分析 | `competitors: list[str]` |
| `stp` | STP分析 | `segments: list[str]` |
| `4p` | 4P分析 | `price_range`, `channels` |
| `swot` | SWOT分析 | `competitors`, `market_trends` |
| `persona` | ペルソナ設計 | `age_range`, `lifestyle_notes` |

各フレームワークは `InputModel` を継承して追加フィールドを定義。

---

## 5. キャッシュ設計（`cache.py`）

### 5.1 採用

`diskcache`（ファイルベース、依存小、TTL対応）をMVPで採用。

### 5.2 キー設計

```
<adapter_name>:<method>:<hash(sorted_params)>
```

例: `narou:search:a1b2c3...`, `kindle_jp:ranking:d4e5f6...`

### 5.3 TTLデフォルト

| 用途 | TTL | 理由 |
|---|---|---|
| 検索結果 | 6時間 | トレンド変動を捉えつつ過剰取得を防ぐ |
| ランキング | 1時間 | Kindleは更新頻度高い |
| 作品詳細 | 24時間 | 変動小 |
| Google Trends | 6時間 | pytrendsの429対策 |

設定ファイルで上書き可能。手動パージ用ツール `purge_cache` も将来提供。

---

## 6. 設定（`config.py`）

### 6.1 優先順位

1. 環境変数（`NOVEL_SEARAH_*`）
2. ユーザー設定ファイル（`~/.config/novel-searah-mcp/config.toml`）
3. デフォルト値

### 6.2 主要設定項目

| キー | 用途 | デフォルト |
|---|---|---|
| `NOVEL_SEARAH_CACHE_DIR` | キャッシュ格納先 | `~/.cache/novel-searah-mcp` |
| `NOVEL_SEARAH_USER_AGENT` | 全HTTP共通のUA | `novel-searah-mcp/<ver> (+github URL)` |
| `NOVEL_SEARAH_PAAPI_*` | Amazon PA-API 関連キー | **初期リリースでは未使用**（§6.3 参照） |
| `NOVEL_SEARAH_RAKUTEN_APP_ID` | 楽天ブックスAPI | なし |
| `NOVEL_SEARAH_LOG_LEVEL` | structlog レベル | `INFO` |

### 6.3 Amazon Kindle アクセス方針

- **初期リリースは `amazon.co.jp` の公開ページ解析のみで実装**
- PA-API は導入しない（契約の前提条件を回避、開発・配布の簡素化）
- 公開ページ取得の範囲は「ランキングページ」「検索結果ページ」「商品詳細ページ」に限定
- User-Agent を明示、robots.txt を尊重、保守的レート（§3.3）、長めのキャッシュTTL
- 将来、PA-API 契約可能なユーザー向けに環境変数での切替えを追加（後続イテレーション）

---

## 7. エラーハンドリング方針

- アダプター層では必ず `AdapterError` 派生に正規化して投げる
- `tools/` 層はエラーをキャッチし、MCPレスポンスとして次を返す:
  - `error.code`: `RATE_LIMITED` / `NOT_FOUND` / `UPSTREAM_UNAVAILABLE` / `VALIDATION_ERROR` / `INTERNAL_ERROR`
  - `error.message`: ユーザー向け説明
  - `error.retry_after_seconds`: レート制限時のみ

---

## 8. テスト戦略

| 種別 | ツール | 対象 |
|---|---|---|
| 単体 | `pytest` | models, frameworks, cache |
| 非同期 | `pytest-asyncio` | adapters |
| 外部API | `vcrpy` または `pytest-httpx` | adapters のカセット記録・再生 |
| 契約 | pydantic バリデーション | tools の入出力 |
| E2E（軽量） | stdio 経由の簡易スモーク | server |

フィクスチャ：各アダプターの代表レスポンスを `tests/fixtures/` に保存。

---

## 9. 未決事項

- [x] Amazon の取得方針 → **公開ページ解析のみで初期リリース**（§6.3）
- [x] なろう小説API のレート → **1 req/sec** を保守的デフォルト（§3.3）
- [x] Markdownテンプレの体裁 → **絵文字・装飾記号なし**（§4.3）
- [ ] 楽天ブックスAPIのカテゴリマッピング（ラノベ/文芸/コミック）
- [ ] ログ出力でPII・原稿情報が混入しないためのサニタイザ
- [ ] Kindle公開ページのHTML構造変化に対する壊れにくい解析戦略（セレクタ抽象化）

---

## 改訂履歴

| 日付 | バージョン | 変更点 |
|---|---|---|
| 2026-04-23 | v0.1 | 初版起票（requirements.md v0.3 と対応） |
| 2026-04-23 | v0.2 | Amazon方針・レート・Markdown規約を確定。§3.3／§4.3／§6.3 を追記 |
