# novel-searah-mcp 要求・要件定義書

> ステータス: **ドラフト v0.2**（2026-04-23 更新）
> 本書は後続イテレーションで追記・修正されることを前提としたリビングドキュメントです。

---

## 1. プロジェクト目的（Why）

ライトノベル／なろう系小説の執筆者・編集者が、
**「作品企画・連載戦略をビジネス／マーケティング視点で立案できる」**
状態をMCP経由で提供する。

- 作家の「感覚」を、再現性のあるフレームワークとデータに橋渡しする
- 昨今の市場動向（Web投稿サイト・電子書籍）を取得し、企画判断の材料にする
- Claude等のMCPクライアントから自然言語で呼び出せる

---

## 2. スコープ

### 2.1 In Scope（初期リリース）

- MCPサーバー本体（stdio / 必要に応じてHTTP）
- ビジネスフレームワーク生成ツール群（3C / STP / 4P / SWOT / ペルソナ 等）
- 情報ソースアダプター群（後述 §5）
- トレンド集計・差別化分析ツール
- ローカル実行での動作

### 2.2 Out of Scope（当面やらない）

- 本文の自動生成・執筆代行（クライアント側LLMに委ねる）
- 有料データベース連携（出版科学研究所 等）
- GUI／Webアプリ提供
- ユーザーの原稿データを外部送信すること

---

## 3. ステークホルダー／想定ユーザー

| 区分 | ペルソナ例 | 主要ニーズ |
|---|---|---|
| 作家（アマ） | なろう投稿者 | ランキング上位傾向、タイトル案、次作テーマ探索 |
| 作家（プロ） | ラノベ作家 | 競合作品分析、読者ペルソナ整理、続刊戦略 |
| 編集者 | ラノベ編集 | 市場ポジショニング、メディアミックス適性評価 |
| マーケ担当 | 出版社宣伝 | 4P整理、プロモ施策立案 |

---

## 4. 要求（ユースケース一覧）

| ID | シーン | 入力 | 期待される出力 |
|---|---|---|---|
| UC-01 | 企画初期のテーマ探索 | ジャンル・キーワード | 最近のトレンドワード、伸びている題材、差別化候補 |
| UC-02 | 読者ペルソナ設計 | 作品設定・想定読者 | STP・ペルソナシート（テンプレ準拠） |
| UC-03 | 競合作品の比較 | 作品タイトル or 設定 | ポジショニングマップ、類似作品、差分 |
| UC-04 | 4P／マーケミックス整理 | 作品情報 | Product/Price/Place/Promotion の下書き |
| UC-05 | SWOT分析 | 作品企画 | 強み・弱み・機会・脅威 |
| UC-06 | タイトル／あらすじ評価 | 候補タイトル | 文字数・キーワード・トレンド接尾辞との適合度 |
| UC-07 | 連載KPI設計 | 作品・目標 | ブクマ／PV／更新頻度のベンチマーク |
| UC-08 | 電子書籍化／メディアミックス適性 | 作品情報 | 電書ランキング類似作品、想定ターゲット媒体 |

---

## 5. 情報ソース（アダプター層）

> **設計方針**: ソースは独立したアダプターとして実装し、後から追加可能にする。
> すべて利用規約・robots.txt・API利用条件を遵守。レート制限・キャッシュを必ず入れる。

### 5.1 初期対応候補

| # | ソース | 取得手段 | 優先度 | 備考 |
|---|---|---|---|---|
| S-01 | 小説家になろう | 公式「なろう小説API」 | 高 | JSON/YAML、規約準拠で安定 |
| S-02 | カクヨム | Web（構造化データ活用） | 中 | 公式API無し。規約確認必須 |
| S-03 | アルファポリス | Web | 中 | 規約確認必須 |
| S-04 | ノベルアップ+ | Web | 低 | 規模小・規約確認必須 |
| S-05 | Amazon Kindle ランキング | PA-API or 公開ページ | 高 | **電子書籍領域の主ソース** |
| S-06 | 楽天Kobo / BookLive / ブックウォーカー | 各社API or 公開ページ | 中 | **電子書籍ソース追加分** |
| S-07 | 出版社新刊情報（MF文庫J・電撃・GA等）| RSS/公開ページ | 中 | レーベル動向把握 |
| S-08 | X（旧Twitter）ハッシュタグ | X API | 低 | 有料APIコスト要検討 |
| S-09 | Google Trends | pytrends 等 | 中 | 題材の検索需要を補完 |

### 5.2 アダプター共通インターフェース（案）

```
Adapter
  - name: str
  - search(query, limit) -> list[Work]
  - ranking(category, period) -> list[Work]
  - detail(id) -> Work
  - health() -> status

Work (共通スキーマ)
  - source, id, title, author, tags[], synopsis
  - metrics: { bookmarks?, points?, reviews?, rank?, sales_rank? }
  - url, updated_at
```

---

## 6. 提供するMCPツール

> **方針**: ビジネス／マーケティングの主要フレームワークは「全部載せ」とする。
> ただし内部実装は `frameworks/` 配下に1ファイル1フレームワークで揃え、
> 共通の `Framework` 基底クラスから派生させることで、後から追加・削除を容易にする。

### 6.1 情報取得・分析系ツール

| Tool名 | 役割 | 主要入力 | 主要出力 |
|---|---|---|---|
| `search_works` | 横断作品検索 | query, sources[] | Work[] |
| `get_ranking` | ランキング取得 | source, category, period | Work[] |
| `analyze_trends` | トレンド抽出 | genre, period | キーワード頻度、急上昇題材 |
| `compare_works` | 競合比較 | 自作品, 比較対象[] | 差分・ポジショニング |
| `evaluate_title` | タイトル評価 | タイトル案[] | スコア・改善示唆 |
| `suggest_kpi` | KPI設計 | 作品・目標 | 指標テンプレ |
| `list_frameworks` | 利用可能なフレームワーク一覧 | — | フレームワーク名・用途 |

### 6.2 ビジネスフレームワーク系ツール（全部載せ）

> すべて `build_<framework>` 命名に統一。入力は「作品情報（設定・ジャンル・ターゲット等）」、
> 出力は「構造化データ（JSON）＋Markdownレポート」の2形態。
> 情報が不足している場合は、LLM側で補完できるようプロンプト用の質問リストを返す。

#### 環境・競合分析系

| Tool名 | フレームワーク | 用途 |
|---|---|---|
| `build_pest` | PEST / PESTEL | 政治・経済・社会・技術（+環境・法律）マクロ環境分析 |
| `build_3c` | 3C | Customer / Competitor / Company |
| `build_5forces` | ファイブフォース | 業界構造分析（新規参入・代替品・買い手・売り手・既存競合） |
| `build_swot` | SWOT / クロスSWOT | 強み・弱み・機会・脅威＋戦略クロス |
| `build_value_chain` | バリューチェーン | 執筆〜販売までの価値連鎖分析 |
| `build_vrio` | VRIO | 経営資源の競争優位性評価 |

#### 顧客理解系

| Tool名 | フレームワーク | 用途 |
|---|---|---|
| `build_stp` | STP | セグメンテーション／ターゲティング／ポジショニング |
| `build_persona` | ペルソナ | 読者ペルソナシート |
| `build_customer_journey` | カスタマージャーニーマップ | 認知〜ファン化の道筋 |
| `build_jtbd` | ジョブ理論（JTBD） | 読者が作品に求める「ジョブ」を分解 |
| `build_empathy_map` | エンパシーマップ | 読者の Think/Feel/See/Hear/Say/Do |
| `build_consumer_behavior` | AIDMA / AISAS / SIPS / DECAX | 消費者行動モデルで導線設計 |

#### 戦略立案系

| Tool名 | フレームワーク | 用途 |
|---|---|---|
| `build_4p` | 4P（または4C / 7P） | Product・Price・Place・Promotion |
| `build_ansoff` | アンゾフマトリクス | 既存/新規 × 市場/作品 の成長戦略 |
| `build_lanchester` | ランチェスター戦略 | 弱者/強者の戦い方選択 |
| `build_blue_ocean` | ブルーオーシャン（ERRC） | Eliminate/Reduce/Raise/Create で差別化 |
| `build_plc` | プロダクトライフサイクル | 作品・ジャンルの成熟度判定 |
| `build_bcg_matrix` | BCGマトリクス | 複数作品のポートフォリオ管理（作家向け） |
| `build_business_model_canvas` | ビジネスモデルキャンバス | 9ブロックでマネタイズ全体像 |
| `build_lean_canvas` | リーンキャンバス | 新作企画を1枚で検証 |
| `build_value_proposition_canvas` | バリュープロポジションキャンバス | 読者の悩み×作品の提供価値 |

#### 小説・コンテンツ特化

| Tool名 | 用途 |
|---|---|
| `build_logline` | ログライン／エレベーターピッチ生成（「○○が××する話」形式） |
| `build_positioning_map` | 2軸ポジショニングマップ（軸候補の提案込み） |
| `build_title_strategy` | タイトル戦略（なろう系接尾辞・キーワード密度・文字数最適化） |
| `build_mediamix_fit` | メディアミックス適性（コミカライズ／アニメ化／電子書籍化） |
| `build_serialization_plan` | 連載計画（更新頻度・話数・区切り・ブクマ誘導ポイント） |

### 6.3 共通出力仕様

- 構造化データ（JSON）: プログラム処理・他フレームワークへの連携用
- Markdownレポート: 人間が読む用、そのまま企画書に貼れる粒度
- 情報不足時は `missing_inputs: [...]` を返し、追加質問案をクライアントに提示させる

---

## 7. 非機能要件

- **プライバシー**: ユーザーの未公開原稿を外部送信しない／ログに残さない
- **コンプライアンス**: 各サイトの利用規約・robots.txt・API利用条件を遵守
- **パフォーマンス**: 単一ツール呼び出しは通常 10 秒以内／並列取得をサポート
- **キャッシュ**: 情報ソース取得結果はローカルキャッシュ（TTL設定可）
- **レート制限**: ソース毎に設定可能、デフォルトは保守的な値
- **拡張性**: アダプター／ツールはプラグイン形式で追加可能
- **テスト容易性**: 外部依存はモック可能な境界設計
- **再現性**: 同一入力・同一キャッシュ条件で同一出力

---

## 8. 技術スタック

| 項目 | 採用 | 備考 |
|---|---|---|
| 言語 | **Python 3.11+** | スクレイピング・データ処理・作家向けツールの親和性 |
| MCP SDK | `mcp`（公式 `modelcontextprotocol/python-sdk`） | stdio / SSE 両対応 |
| パッケージ管理 | `uv` | 高速・lockファイル管理 |
| HTTPクライアント | `httpx`（async対応） | 並列取得を想定 |
| HTML解析 | `selectolax`（高速）+ フォールバックで `beautifulsoup4` | |
| データスキーマ | `pydantic` v2 | 入出力バリデーション |
| キャッシュ | `diskcache` または SQLite | TTL付き |
| ロギング | `structlog` | 構造化ログ |
| テスト | `pytest` + `pytest-asyncio` + `vcrpy`（外部APIリプレイ） | |
| Lint/Format | `ruff` + `mypy` | |
| 配布 | **PyPI** ＋ ローカル実行サポート | `uvx novel-searah-mcp` で即実行可能を目指す |

### 8.1 想定ディレクトリ構成（暫定）

```
novel-searah-mcp/
├── pyproject.toml
├── README.md
├── docs/
│   └── requirements.md
├── src/
│   └── novel_searah_mcp/
│       ├── __init__.py
│       ├── server.py            # MCPエントリポイント
│       ├── config.py
│       ├── models.py            # Work等の共通スキーマ（pydantic）
│       ├── cache.py
│       ├── adapters/            # 情報ソース毎
│       │   ├── base.py
│       │   ├── narou.py
│       │   ├── kakuyomu.py
│       │   ├── alphapolis.py
│       │   ├── novelup.py
│       │   ├── kindle.py
│       │   ├── kobo.py
│       │   ├── booklive.py
│       │   ├── bookwalker.py
│       │   ├── publishers.py
│       │   ├── twitter.py
│       │   └── google_trends.py
│       ├── frameworks/          # ビジネスフレームワーク毎
│       │   ├── base.py          # Framework基底クラス
│       │   ├── pest.py
│       │   ├── three_c.py
│       │   ├── five_forces.py
│       │   ├── swot.py
│       │   ├── value_chain.py
│       │   ├── vrio.py
│       │   ├── stp.py
│       │   ├── persona.py
│       │   ├── customer_journey.py
│       │   ├── jtbd.py
│       │   ├── empathy_map.py
│       │   ├── consumer_behavior.py
│       │   ├── four_p.py
│       │   ├── ansoff.py
│       │   ├── lanchester.py
│       │   ├── blue_ocean.py
│       │   ├── plc.py
│       │   ├── bcg_matrix.py
│       │   ├── business_model_canvas.py
│       │   ├── lean_canvas.py
│       │   ├── value_proposition_canvas.py
│       │   ├── logline.py
│       │   ├── positioning_map.py
│       │   ├── title_strategy.py
│       │   ├── mediamix_fit.py
│       │   └── serialization_plan.py
│       └── tools/               # MCPツール登録
│           ├── __init__.py
│           ├── search.py
│           ├── trends.py
│           └── frameworks.py
└── tests/
    ├── adapters/
    ├── frameworks/
    └── fixtures/                # vcrpy カセット
```

---

## 9. リスクと対応

| リスク | 対応 |
|---|---|
| サイト側の規約変更・構造変更 | アダプターを疎結合化、壊れた時だけ修正 |
| レート制限違反 / IPブロック | 保守的レート・ユーザーエージェント明示・キャッシュ徹底 |
| スクレイピング法務リスク | 公式APIを最優先、Web取得は公表情報の範囲・規約準拠 |
| 著作権（あらすじ等の扱い）| 引用要件を満たす範囲、本文丸写し禁止 |
| トレンド情報の鮮度 | キャッシュTTLを適切化、手動再取得コマンド提供 |

---

## 10. 未決事項 / 次のアクション

- [x] 技術スタック確定（**Python 3.11+** / uv / 公式 `mcp` SDK）
- [x] 配布形態確定（**PyPI ＋ ローカル実行**、`uvx` 対応を目指す）
- [x] フレームワーク方針（**全部載せ**、§6.2 参照）
- [x] ディレクトリ構成・モジュール設計（§8.1 暫定案）
- [ ] 電子書籍ソースの優先順位（Kindle 最優先でよいか、Kobo/BookLive/BookWalker の順序）
- [ ] MVPスコープの絞り込み（最小構成で何を出すか）
- [ ] アダプター・フレームワーク基底クラスのインターフェース詳細設計
- [ ] キャッシュ戦略（TTLデフォルト、キー設計）
- [ ] 設定ファイル形式（環境変数 / TOML / JSON）

---

## 改訂履歴

| 日付 | バージョン | 変更点 |
|---|---|---|
| 2026-04-23 | v0.1 | 初版起票 |
| 2026-04-23 | v0.2 | 技術スタックを Python に確定。フレームワークを全部載せに拡張（§6.2）。ディレクトリ構成案（§8.1）を追記 |
