# AIエージェントによるテスト自動化パイプライン

**作成日**: 2026-04-27
**ステータス**: 設計確定版
**関連ドキュメント**: [../../CLAUDE.md](../../CLAUDE.md)（テスト規約の詳細）

### 改訂履歴

| 日付 | 改訂内容 |
|------|---------|
| 2026-06-19 | 結合テストの証跡定義を強化。スクリーンショットに加え、開発者コンソール・DBレコード・コンテナログ・DBログの5種を必須の収集・照合対象とし、正常系/異常系の判定ルールを明記（13章 新設） |

---

## 目次

- [1. 概要](#1-概要)
- [2. 用語集](#2-用語集)
- [第1部：単体テストパイプライン](#第1部単体テストパイプライン)
  - [3. パイプライン全体図](#3-パイプライン全体図)
  - [4. エージェント構成](#4-エージェント構成)
  - [5. 各フェーズの詳細](#5-各フェーズの詳細)
  - [6. 人間レビュー](#6-人間レビュー)
  - [7. 品質ゲート](#7-品質ゲート)
  - [8. エラーハンドリングとエスカレーション](#8-エラーハンドリングとエスカレーション)
- [第2部：結合テストパイプライン](#第2部結合テストパイプライン)
  - [9. パイプライン全体図](#9-パイプライン全体図)
  - [10. エージェント構成](#10-エージェント構成)
  - [11. Markdown変換仕様](#11-markdown変換仕様)
  - [12. agent-browser によるテスト実行手順](#12-agent-browser-によるテスト実行手順)
  - [13. 結合テストの証跡定義](#13-結合テストの証跡定義)
- [付録](#付録)
  - [A. 単体テスト vs 結合テスト の比較](#a-単体テスト-vs-結合テスト-の比較)
  - [B. 実行環境](#b-実行環境)
  - [C. テストコード規約（CLAUDE.md からの参照）](#c-テストコード規約clauemd-からの参照)

---

## 1. 概要

WEKO3の開発プロセスにおいて、単体テストおよび結合テストの工程をAIエージェントと人間の協業で効率化するためのパイプライン設計である。

- **単体テストパイプライン**: 詳細設計書からテスト仕様書・テストコードをエージェントが生成し、人間がレビュー・実行・修正・最終確認を行う
- **結合テストパイプライン**: Excelのテスト仕様書をMarkdownに変換し、agent-browserでブラウザ操作を直接実行・検証する

単体テストではエージェントの主担当を「テスト仕様書・テストコードの初期生成」に限定し、レビュー、pytest実行、修正、最終確認は人間が行う。結合テストではエージェントによる検証を継続する。

## 2. 用語集

| 用語 | 説明 |
|------|------|
| Backend Architect | Python/Flask/Invenioのアーキテクチャを理解するエージェント。テスト仕様書・テストコードの生成を担当 |
| Code Reviewer | コードの正しさ・保守性・セキュリティ・パフォーマンスに焦点を当てたレビューを行うエージェント |
| EvidenceQA | 証拠偏重のQAエージェント。agent-browserを使用してブラウザ操作を実行し、スクリーンショットに加え開発者コンソール・DBレコード・コンテナログ・DBログの5種の証跡を収集・照合（13章 参照） |
| Reality Checker | 証拠ベースで最終判定を行うエージェント。デフォルトで「NEEDS WORK」を出力。スクリーンショット単独での合格判定は認めない |
| 証跡（エビデンス） | 結合テストでフロントエンド・バックエンド双方の動作を裏付ける観測データ。スクリーンショット／開発者コンソール／DBレコード／コンテナログ／DBログの5種（13章 参照） |
| agent-browser | ブラウザ自動化ツール。ナビゲーション、フォーム入力、スクリーンショット撮影などを自動実行 |
| 分岐ID | 条件分岐に付与する一意の識別子（B01, B02, ...）。テスト網羅の追跡に使用 |
| パッチパス | Pythonの`unittest.mock.patch`で使用する対象モジュールのフルパス |
| WEKO_BASE_URL | WEKO3のアクセスURL（環境変数） |

---

# 第1部：単体テストパイプライン

## 3. パイプライン全体図

```
  ① 詳細設計書読み込み
    Backend Architect
          ▼
  ② テスト仕様書生成
    Backend Architect
          ▼
  🔴 人間レビュー #1（テスト仕様書）
    ドキュメントコメントでフィードバック
          ▼
  ③ テストコード生成
    Backend Architect
          ▼
  🔴 人間レビュー #2（テストコード）
    ドキュメントコメントでフィードバック
          ▼
  ④ pytest / coverage 実行
    人間
          ▼
  ⑤ テストコード修正
    人間
          ▼
  ⑥ 必要時のみAI支援
    Backend Architect または Code Reviewer
          ▼
  🔴 人間最終確認
    人間
```

## 4. エージェント構成

| フェーズ | 担当 | 入力 | 出力 |
|----------|------|------|------|
| ① 詳細設計書読み込み | Backend Architect | 詳細設計書、プログラム設計書、関連仕様 | テスト観点、条件分岐、外部依存候補 |
| ② テスト仕様書生成 | Backend Architect | 詳細設計書 + テスト規約 | `<モジュール>_test_spec.md` |
| 🔴 人間レビュー #1 | 人間 | テスト仕様書 | コメント付き修正指示、または承認 |
| ③ テストコード生成 | Backend Architect | レビュー済みテスト仕様書 + 既存 `conftest.py` + 必要最小限の対象コード | `tests/test_<モジュール>.py` |
| 🔴 人間レビュー #2 | 人間 | テストコード | コメント付き修正指示、または承認 |
| ④ pytest / coverage 実行 | 人間 | テストコード、対象ソース | pytest結果、coverage結果 |
| ⑤ テストコード修正 | 人間 | pytest結果、coverage結果、レビュー指摘 | 修正済みテストコード |
| ⑥ 必要時のみAI支援 | Backend Architect または Code Reviewer | 失敗ログの該当部分、対象テスト、関連ソース | 原因候補、修正方針、必要に応じた修正案 |
| 🔴 人間最終確認 | 人間 | pytest結果、coverage結果、レビュー結果 | 完了判断 |

### エージェント選択の理由

- **Backend Architect**: Python / Flask / Invenio のアーキテクチャ理解があるため、詳細設計書から正しいモック対象を特定し、CLAUDE.mdの「パッチパス基本原則」に従ったテストコードを生成できる
- **Code Reviewer**: 正しさ・保守性・セキュリティ・パフォーマンスに焦点を当てた建設的なフィードバックが可能。pytestの失敗結果を構造的に分析し、具体的な修正指示を出せる
- **人間レビュー**: テスト仕様書およびテストコードの妥当性の品質担保の中心。AIレビューは役割が重複し、トークン消費に対する効果が限定的であるため廃止
- **人間最終確認**: pytest結果、coverage結果、レビュー状況の最終確認は人間が行う。エージェントに実施させると追加のトークン消費が発生するため

## 5. 各フェーズの詳細

### 5.1 詳細設計書読み込み（Backend Architect）

対象モジュールの詳細設計書・プログラム設計書などの設計資料を読み込み、以下の情報を抽出する：

- テスト観点の整理
- 条件分岐（if/elif/else）の列挙 → 分岐IDを付与（B01, B02, ...）
- 外部依存候補の特定（DBアクセス、APIコールなど）
- 例外ハンドラ（try/except）の特定

> **注意**: ソースコードを主入力にすると、実装追認型のテストになりやすく、設計仕様に対する検証という目的が弱くなる。そのため、テスト仕様書生成の主入力は設計資料とし、ソースはテストコード生成時に必要最小限（patch path、関数名、import位置、fixture利用可否の確認）に限定する。

### 5.2 テスト仕様書生成（Backend Architect）

[../../CLAUDE.md](../../CLAUDE.md) の規約に従い、以下の必須要素を含むテスト仕様書を生成する：

- **テストケース表**: テストケースID、テスト内容、入力内容、期待結果、モック対象、備考
- **モック対象一覧表**: モジュールパス、モック理由
- **分岐マップ**: 各分岐ID × True/False × 対応テストケースID

出力先: 対象モジュールの `weko_*/` ディレクトリ直下

### 5.3 テストコード生成（Backend Architect）

レビュー済みのテスト仕様書に基づき、pytest テストコードを生成する。

- ファイル名: `tests/test_<対象モジュール名>.py`
- 1テストケース = 1メソッド（メソッド名はケースNoを含めず内容を表す英語名）
- クラス `Test<TargetMethodName>` にメソッドをまとめる
- `conftest.py` 既存のフィクスチャを優先して使用
- patch path、実際の関数名、import位置、fixture利用可否を確認するため、必要最小限の対象コードを参照

### 5.4 pytest / coverage 実行（人間）

```bash
# テスト収集確認
docker exec weko-web-1 bash -c \
  "cd /code/modules/weko-search-ui && \
   /home/invenio/.virtualenvs/invenio/bin/pytest tests/test_<ファイル名>.py --collect-only -q"

# テスト実行（カバレッジなし）
docker exec weko-web-1 bash -c \
  "cd /code/modules/weko-search-ui && \
   /home/invenio/.virtualenvs/invenio/bin/pytest tests/test_<ファイル名>.py -vv"
```

- pytest を実行し、結果を確認
- coverage を実行し、カバレッジ結果を確認

### 5.5 テストコード修正（人間）

- pytestの失敗結果、coverage結果、レビュー指摘に基づいてテストコードを修正
- 修正後は再度 pytest / coverage を実行

### 5.6 必要時のみAI支援（Backend Architect または Code Reviewer）

pytest失敗時、原則として人間がまず確認する。人間だけで原因特定または修正方針の判断が難しい場合に限り、エージェントに以下の情報を渡す：

- 失敗したテスト名
- assert差分
- スタックトレースの該当部分
- 対象テストコードの該当箇所
- 対象ソースコードの該当箇所
- 期待仕様が分かる詳細設計書の該当箇所

エージェントの出力は、原則として以下に限定する：

- 失敗原因の候補
- 設計書・テスト仕様書・実装の不整合箇所
- 修正方針
- 必要に応じた最小限の修正案

> **利用シーン**: patch path が正しいか判断しにくい場合、mock chain や fixture の構成が複雑な場合、pytest失敗原因の切り分けに時間がかかる場合、設計書・テスト仕様書・実装のどこに不整合があるか整理したい場合

## 6. 人間レビュー

### 6.1 レビュー #1: テスト仕様書レビュー

| 項目 | 内容 |
|------|------|
| 確認箇所 | 分岐マップの網羅性、テストケースの妥当性、モック対象の適切さ |
| フィードバック方法 | テスト仕様書（Markdown）にコメントとして追記 |

### 6.2 レビュー #2: テストコードレビュー

| 項目 | 内容 |
|------|------|
| 確認箇所 | パッチパスの正確性、モックチェーンの記法、例外ハンドリングの網羅性、CLAUDE.md 規約の遵守 |
| フィードバック方法 | テストコード（`.py`）にコメントとして追記 |

### 6.3 コメント形式

```markdown
## レビューコメント
> 🟡 [レビュー者: 氏名] 指摘内容
> → 修正指示
```

## 7. 品質ゲート

| ゲート | 判定者 | 条件 |
|--------|--------|------|
| テスト仕様書レビュー | 人間 | 詳細設計書に対してテスト観点・条件分岐・期待値に抜け漏れがないこと |
| テストコードレビュー | 人間 | テスト仕様書に沿っていること、patch path / mock / fixture が妥当であること |
| pytest実行 | 人間 | 全テストケース PASS |
| coverage確認 | 人間 | プロジェクトで定めたcoverage基準を満たすこと |
| 最終確認 | 人間 | pytest結果、coverage結果、レビュー指摘の対応が完了していること |

## 8. エラーハンドリングとエスカレーション

### 8.1 pytest 実行失敗の分類

| 失敗タイプ | 原因例 | 対応 |
|-----------|--------|------|
| モック設定ミス | `AttributeError`, `patch` パス不正 | パッチパスの再確認（CLAUDE.mdの原則に従う） |
| 期待値ミス | `AssertionError` | 詳細設計書のロジックを再確認 → 期待値の修正 |
| 例外テスト失敗 | 例外の発生箇所が異なる | CLAUDE.mdの例外パターン表を参照 → itemの状態を調整 |
| 接続エラー | `ConnectionError`, `SQLAlchemyError` | ログモックを挿入（CLAUDE.mdの対処法に従う） |

### 8.2 必要時のAI支援による原因調査

人間だけで原因特定または修正方針の判断が難しい場合に限り、Backend Architect または Code Reviewer に以下の情報を渡す：

- 失敗したテスト名
- assert差分
- スタックトレースの該当部分
- 対象テストコードの該当箇所
- 対象ソースコードの該当箇所
- 期待仕様が分かる詳細設計書の該当箇所

エージェントの出力は、原則として以下に限定する：

- 失敗原因の候補
- 設計書・テスト仕様書・実装の不整合箇所
- 修正方針
- 必要に応じた最小限の修正案

---

# 第2部：結合テストパイプライン

## 9. パイプライン全体図

```
  ① Excel → Markdown 変換（人力 OR スクリプト）
    → Excelの結合テスト仕様書をMarkdownに変換
          ▼
  🔴 人間レビュー（Markdown変換確認）
    → 変換後の内容がExcelと一致することを確認
          ▼
  ② テスト実行（EvidenceQA ＋ agent-browser）
    → Markdownのテストシナリオを読み込む
    → agent-browserでブラウザ操作を直接実行
    → 各ステップで5種の証跡を収集（13章 参照）
       スクリーンショット／開発者コンソール／DBレコード／
       コンテナログ／DBログ
    → 期待結果・判定ルールとの照合 → 3〜5件の問題をデフォルトで発見
          ▼
  ③ 結果判定・修正ループ（Code Reviewer）
    → EvidenceQAの複数証跡を突き合わせて原因分析
    → 問題があれば修正指示（最大3回）
          ▼
  ④ 最終検証（Reality Checker）
    → 5種の証跡を相互照合（フロント・バックエンド双方）
    → 判定ルール（13.2）を満たすか確認
    → PASS / NEEDS WORK 判定
```

## 10. エージェント構成

| フェーズ | エージェント | ツール | 入力 | 出力 |
|----------|-------------|--------|------|------|
| ① Excel→Markdown変換 | 人力 OR スクリプト | - | Excel テスト仕様書 | Markdown テスト仕様書 |
| ② テスト実行 | EvidenceQA | agent-browser | Markdown テスト仕様書 | 5種の証跡（スクリーンショット／開発者コンソール／DBレコード／コンテナログ／DBログ）、問題リスト |
| ③ 結果判定・修正 | Code Reviewer | - | 5種の証跡、問題リスト | 原因分析、修正指示 |
| ④ 最終検証 | Reality Checker | - | 全証跡（5種） | 判定ルール（13.2）に基づく PASS / NEEDS WORK 判定 |

### エージェント選択の理由

- **EvidenceQA**: スクリーンショット偏重のQAスペシャリスト。デフォルトで3〜5件の問題を発見しようとする姿勢と、「全ての主張に証拠を要求」する性質が、結合テストのブラウザ操作検証に適合。スクリーンショットだけでなく、開発者コンソール・DBレコード・コンテナログ・DBログを併せて収集し、フロントエンド・バックエンド双方の正常動作を裏付ける（13章 参照）
- **agent-browser**: ブラウザ自動化ツール。ナビゲーション、フォーム入力、ボタンクリック、スクリーンショット撮影、データ抽出に加え、開発者コンソール（コンソールエラー・ネットワークタブ）の取得を自動実行
- **Code Reviewer**: 単体テストパイプラインと同様に、正しさに焦点を当てた原因分析と修正指示を担当。複数の証跡ソースを突き合わせて、フロント側・バックエンド側のどこに原因があるかを切り分ける
- **Reality Checker**: 証拠ベースの最終判定（デフォルト NEEDS WORK）。スクリーンショット単独での合格判定は認めず、13.2 の判定ルールを全て満たすことを要求する

## 11. Markdown変換仕様

### 変換前のExcel構造

- ステップ単位で記載（1操作 = 1行）
- 列: テストID、ステップNo、操作内容、期待結果

### 変換後のMarkdown形式

```markdown
# 結合テスト仕様書

## テストケース一覧

| テストID | テスト名 | 対象機能 | 優先度 |
|---------|---------|---------|-------|
| IT-01-01 | ログインとWorkflowアクセス | 認証 | 高 |
| IT-02-01 | アイテム登録フロー | デポジット | 高 |

---

## IT-01-01: ログインとWorkflowアクセス

**前提条件**:
- テスト用アカウントが存在すること
- WEKOシステムが起動していること

**テストデータ**:
- メール: `test@weko3.example.org`
- パスワード: `testpassword`

| ステップ | 操作 | 期待結果 |
|---------|------|---------|
| 1 | トップ画面にアクセス | WEKOのトップ画面が表示される |
| 2 | 「Log in」リンクをクリック | ログイン画面に遷移する |
| 3 | メールアドレス・パスワードを入力し「Log In」をクリック | 認証成功后、トップ画面に戻る |
| 4 | 「Workflow」リンクをクリック | Workflow画面に遷移する |

**片付け**:
- 特になし（ログイン状態は保持可）
```

## 12. agent-browser によるテスト実行手順

### 12.1 コンテナの準備

```bash
# agent-browser がインストールされたコンテナを起動
docker run -d \
  --name weko-agent-browser-container \
  --network host \
  weko-agent-browser:latest

# コンテナ内の agent-browser を確認
docker exec weko-agent-browser-container which agent-browser
```

### 12.2 EvidenceQA によるテスト実行パターン

EvidenceQA は agent-browser のコマンドを使用して、Markdown のテストシナリオを1ステップずつ実行する。

#### パターン 1: ページアクセスの確認

```bash
# トップページへのアクセス
docker exec weko-agent-browser-container agent-browser open '$WEKO_BASE_URL' && \
docker exec weko-agent-browser-container agent-browser wait --load networkidle && \
docker exec weko-agent-browser-container agent-browser screenshot --full /tmp/test-it01-01-homepage.png

# ページタイトルの確認
docker exec weko-agent-browser-container agent-browser get title
# → 期待: "WEKO3" または類似
```

#### パターン 2: ログイン操作

```bash
# ログインリンクをクリック（snapshotでインタラクティブ要素を取得）
docker exec weko-agent-browser-container agent-browser snapshot -i
# → 「Log in」リンクの ref を取得（例: @e3）

docker exec weko-agent-browser-container agent-browser click @e3
docker exec weko-agent-browser-container agent-browser wait --load networkidle

# ログインフォームへの入力
docker exec weko-agent-browser-container agent-browser snapshot -i
# → メールアドレス・パスワードの入力フィールドの ref を取得

docker exec weko-agent-browser-container agent-browser fill @e1 '$WEKO_TEST_EMAIL'
docker exec weko-agent-browser-container agent-browser fill @e2 '$WEKO_TEST_PASSWORD'
docker exec weko-agent-browser-container agent-browser click @e4  # Log In ボタン
docker exec weko-agent-browser-container agent-browser wait --load networkidle

# 認証後の状態を確認（スクリーンショット）
docker exec weko-agent-browser-container agent-browser screenshot --full /tmp/test-it01-02-logged-in.png
```

#### パターン 3: ナビゲーション操作

```bash
# Workflow へのアクセス
docker exec weko-agent-browser-container agent-browser snapshot -i
# → 「Workflow」リンクの ref を取得

docker exec weko-agent-browser-container agent-browser click @e5  # Workflow リンク
docker exec weko-agent-browser-container agent-browser wait --load networkidle
docker exec weko-agent-browser-container agent-browser screenshot --full /tmp/test-it01-03-workflow.png

# URL の確認
docker exec weko-agent-browser-container agent-browser get url
# → 期待: "*workflow*" を含むURL
```

#### パターン 4: テキスト検索による操作

```bash
# テキスト検索で要素を特定してクリック
docker exec weko-agent-browser-container agent-browser find text "Search" click

# ラベルで入力フィールドを特定
docker exec weko-agent-browser-container agent-browser find label "Email" fill '$WEKO_TEST_EMAIL'
```

### 12.3 エビデンス収集のルール

スクリーンショットの撮影タイミングは以下の通り。スクリーンショット以外の証跡（開発者コンソール／DBレコード／コンテナログ／DBログ）の収集対象・収集方法は [13章 結合テストの証跡定義](#13-結合テストの証跡定義) を参照する。

| タイミング | スクリーンショット撮影タイミング | ファイル名規則 |
|-----------|----------------------------------|---------------|
| 各テストケース開始時 | テスト対象ページにアクセス直後 | `test-{テストID}-before.png` |
| 各操作ステップ後 | 重要な操作（クリック・入力）完了後 | `test-{テストID}-step{番号}.png` |
| テストケース終了時 | 最終状態 | `test-{テストID}-after.png` |
| 失敗時 | エラー発生時 | `test-{テストID}-error-step{番号}.png` |

> **注意**: スクリーンショットは画面表示の視覚的証跡であり、それ単独で正常系・異常系の合否を判定してはならない。必ず13章の5種の証跡を収集・照合し、13.2 の判定ルールに従って合否を決定する。

### 12.4 失敗時の対応

```bash
# 1. 現在のページ状態をキャプチャ
docker exec weko-agent-browser-container agent-browser screenshot --annotate /tmp/test-error-annotate.png

# 2. ページのテキスト内容を抽出
docker exec weko-agent-browser-container agent-browser get text body > /tmp/test-error-page.txt

# 3. コンソールエラー・ネットワークログを確認
docker exec weko-agent-browser-container agent-browser inspect

# 4. アプリケーション（Flask/Invenio）コンテナのログを確認
docker logs --tail 200 weko-web-1 > /tmp/test-error-container.log

# 5. DBログ・DBレコードの状況を確認（13章 参照）
```

失敗時は、上記に加えて13章の5種の証跡をすべて収集し、フロントエンド・バックエンドのどちらに原因があるかを切り分けられるようにする。EvidenceQA はこれらのエビデンスを Code Reviewer に提供し、原因分析を依頼する。

### 12.5 セッション管理

```bash
# テスト実行後のブラウザセッションを閉じる
docker exec weko-agent-browser-container agent-browser close --all

# コンテナのクリーンアップ（必要に応じて）
docker stop weko-agent-browser-container && docker rm weko-agent-browser-container
```

### 12.6 認証状態の保持

テストケース間でログイン状態を保持する場合、セッション機能を使用する：

```bash
# 初回ログイン後、セッションを保存
docker exec weko-agent-browser-container agent-browser --session-name weko-test state save /tmp/weko-auth.json

# 以降のテストでセッションを復元
docker exec weko-agent-browser-container agent-browser --session-name weko-test state load /tmp/weko-auth.json
docker exec weko-agent-browser-container agent-browser open '$WEKO_BASE_URL'
```

## 13. 結合テストの証跡定義

結合テスト（EvidenceQA / agent-browser / Reality Checker による検証フェーズ）では、スクリーンショットのみを証跡とすることを禁止する。スクリーンショットは画面表示の視覚的証跡にすぎず、バックエンド側（API・DB・ログ）が正常に動作していることまでは証明できないためである。

フロントエンド・バックエンド双方が正常に動作していることを証明するため、以下の5種の証跡を**必須の収集・照合対象**とし、13.2 の判定ルールに従って合否を決定する。

### 13.1 収集・照合する証跡ソース

| No | 証跡ソース | 収集対象 | 主な収集手段 | 確認の観点 |
|----|-----------|---------|-------------|-----------|
| 1 | スクリーンショット | 画面表示（操作前後・各ステップ・失敗時） | `agent-browser screenshot`（12.3 参照） | 画面表示が期待通りか（視覚的証跡） |
| 2 | ブラウザ開発者コンソール | コンソールエラーの有無、ネットワークタブのAPIリクエスト/レスポンス（ステータスコード・レスポンスボディ） | `agent-browser inspect` / ネットワークログ取得 | JSエラーが出ていないか、APIが期待ステータス・期待ボディを返しているか |
| 3 | DBテーブルのレコード状況 | 操作前後のレコード状態（INSERT/UPDATE/DELETE が期待通り反映されているか） | `docker exec` 経由のSQL（操作前後で対象テーブルを取得し差分を比較） | 期待レコードが存在するか／不正なレコードが残っていないか |
| 4 | コンテナログ | アプリケーション（Flask/Invenio）コンテナのログ | `docker logs weko-web-1` | エラー・例外スタックトレースが出ていないか |
| 5 | DBログ | DB側のエラーログ・スロークエリ・制約違反等 | DBコンテナのログ（`docker logs`）／DBログファイル | DBエラー・制約違反・スロークエリが出ていないか |

> **収集タイミング**: 各テストケースについて、操作の前後で上記5種を収集する。DBレコード（No.3）は「操作前」「操作後」の両方を取得し、INSERT/UPDATE/DELETE の差分を比較することで、期待した変更が反映されたか／不正な変更が残っていないかを確認する。

### 13.2 判定ルール

スクリーンショットだけでの合否判定は不可とする。正常系・異常系それぞれ、以下を**すべて**満たした状態を証跡とする。

#### 13.2.1 正常系の合格証跡

フロントエンド・バックエンドの**どちらにもエラーがなく正常に実行されている様子**を証跡とする。具体的には以下を全て満たすこと。

| # | 証跡ソース | 合格条件 |
|---|-----------|---------|
| 1 | スクリーンショット | 画面表示が期待通りであること |
| 2 | 開発者コンソール | コンソールエラーがないこと／APIが期待ステータス（2xx）を返していること |
| 3 | DBレコード | DBに期待レコードが存在すること（期待した INSERT/UPDATE/DELETE が反映されていること） |
| 4 | コンテナログ | コンテナログにエラー・例外が出ていないこと |
| 5 | DBログ | DBログにエラー・制約違反等が出ていないこと |

> 上記5項目を全て満たして初めて正常系合格とする。スクリーンショットが期待通りでも、コンソールエラーがある／APIが2xxを返していない／DBに期待レコードがない／ログにエラーがある場合は**不合格**とする。

#### 13.2.2 異常系の合格証跡

その挙動の**根拠となるもの**を証跡とする。具体的には以下を満たすこと。

| # | 証跡ソース | 合格条件 |
|---|-----------|---------|
| 1 | スクリーンショット | 期待したエラーメッセージ／トースト表示が出ていること |
| 2 | 開発者コンソール | 期待したエラーレスポンス（4xx/5xx等）が返っていること |
| 3 | DBレコード | DBがロールバックされ、不正なレコードが残っていないこと |
| 4・5 | コンテナログ／DBログ | ログに想定内のエラーが記録されていること |

> 異常系では「エラーが起きること自体」だけでなく、「想定したエラーが、想定した箇所（フロント表示・APIレスポンス・DB状態・ログ）で観測できること」を根拠として求める。想定外の箇所でエラーが出ている場合や、ロールバックされず不正レコードが残っている場合は**不合格**とする。

---

# 付録

## A. 単体テスト vs 結合テスト の比較

| 項目 | 単体テストパイプライン | 結合テストパイプライン |
|------|---------------------|---------------------|
| 入力 | 詳細設計書・プログラム設計書 | Excel テスト仕様書 → Markdown |
| テスト生成 | Backend Architect（テスト仕様書＋pytestコード） | なし（Markdownを直接実行） |
| コードレビュー | 人間レビュー（仕様書＋コード） | なし |
| テスト実行 | 人間（docker exec） | EvidenceQA（agent-browser） |
| 修正 | 人間（必要時にAI支援） | Code Reviewer（原因分析・修正指示） |
| エビデンス | pytestログ、カバレッジ | 5種の証跡（スクリーンショット／開発者コンソール／DBレコード／コンテナログ／DBログ。13章 参照） |
| 最終検証 | 人間 | Reality Checker（13.2 の判定ルールに基づく） |

## B. 実行環境

### 単体テスト

| 項目 | 値 |
|------|-----|
| pytest 実行 | `docker exec weko-web-1` 内（webコンテナ必須） |
| Python バージョン | 3.6 |
| pytest バージョン | 4.6.x |
| フレームワーク | Flask 1.0.4 / Invenio 3 |

### 結合テスト

| 項目 | 値 |
|------|-----|
| ブラウザ | Chromium（headlessモード） |
| 対象システム | WEKO3 インスタンス（`WEKO_BASE_URL`） |
| 認証情報 | `WEKO_TEST_EMAIL`, `WEKO_TEST_PASSWORD` |
| agent-browser コンテナ | `weko-agent-browser:latest`（`--network host`） |

## C. テストコード規約（CLAUDE.md からの参照）

詳細は [../../CLAUDE.md](../../CLAUDE.md) を参照。以下は概要。

### フィクスチャ選択

| 必要なもの | 使用フィクスチャ |
|------------|-----------------|
| Flaskアプリコンテキスト + リクエストコンテキスト | `i18n_app` |
| DBセッション | `db`（`i18n_app` に追加） |
| ESに実レコードが必要な場合 | `es_records` |

### パッチパスの基本原則

- 対象モジュール内でインポートされた名前を起点にする
- 例: `utils.py` が `from weko_deposit.api import WekoRecord` している場合 → `weko_search_ui.utils.WekoRecord`

### モックのチェーン記法

```python
mock_pid_model.query.filter_by.return_value.first.return_value = mock_pid
mock_versioning_cls.return_value.last_child.object_uuid = "uuid-last"
mock_refs.return_value.all.return_value = []
```

### 例外ハンドリングのテストパターン

| item の状態 | 推奨する例外発生箇所 |
|------------|----------------------|
| `status="new"` で id を持たせたい | `create_deposit` をモック → `register_item_metadata` で例外発生 |
| `status="update"` で id を持たせたくない（`id=None`） | `handle_check_item_is_locked` で例外発生 |

`status="new"` のパスでは `handle_check_item_is_locked` は呼ばれない点に注意。
