# AGENTS.md

## プロジェクト概要 / Overview
- WEKO3は研究成果の公開を行うためのリポジトリソフトウェアである。Git等の所謂コードのためのリポジトリとは異なるソフトウェアで、ウェブデータベースアプリケーションに近い概念のソフトウェアである。基本的な機能は研究成果とメタデータと呼ばれる研究成果の説明情報を一緒に保存し、表示、検索、配布する機能がある。外部システム連携のためのAPIを備える。
- **フレームワーク(バックエンド)**: Invenio 3. Invenio3は Flask 1.0.4 をベースにしている。(Python 3.6)
- **フレームワーク（フロントエンド）**: React, Anguler JS, JQuery
- **利用ミドルウェア**: PostgreSQL 12.x(データベース), Pgpool-II 4.2.2(データベースクラスタ用), Elasticsearch 6.8.23(検索用), Redis 7.4.1(セッション、キャッシュ管理用), RabbitMQ 4.0.2(メッセージキューイング用), nginx 1.20.1(ウェブサーバ用、shibboleth-sp組み込み), CNRI Handle Server(CNRIハンドル発行用), MongoDB(一部モジュール用)
- **主要ライブラリ**: Invenio 3 Framework(API,Web API用), Celery + RabbitMQ（タスクキュー）
- **リポジトリ構成**: モノレポ構成。`modules/invenio-*`（本家Invenioのフォーク/パッチ版）と `modules/weko-*`（WEKO固有機能）に、独立してバージョン管理されたPythonパッケージが多数配置されている（それぞれ独自の `setup.py`, `tox.ini`, `tests/` を持つ）。`modules/cookiecutter-weko-module` は新規 `weko-*` モジュールをこの構成でひな形生成するためのテンプレート。`modules/weko-workspace` はそれ自身のPythonパッケージを持たず、インスタンス全体の集約用パッケージとして扱う。
  各モジュール（`weko_<name>/`）は以下の共通構成を持つ。
  - `ext.py` — Flask拡張クラス（`WekoXxx`）。`setup.py` の `invenio_base.apps` / `invenio_base.api_apps` エントリポイントで登録され、集約Invenioアプリに組み込まれる（直接importされるのではない）
  - `config.py` — モジュールのデフォルト設定値（`scripts/instance.cfg` で上書き可能）
  - `models.py` — SQLAlchemyモデル
  - `api.py` — 他モジュールから利用される公開Python API（ビジネスロジック）
  - `views.py` / `rest.py` / `admin.py` — それぞれUI画面, REST API, Flask-Admin画面用のBlueprint
  - `tasks.py` — Celeryタスク（`invenio_celery.tasks` エントリポイントで登録）
  - `cli.py` — Flask CLIサブコマンド（`flask.commands` エントリポイントで登録）
  - `alembic/` — モジュールごとのDBマイグレーション（Alembic/SQLAlchemy-Continuum）
  - `assets/`, `templates/`, `translations/` — フロントエンド資材（webpackバンドル）, Jinjaテンプレート, 多言語化メッセージカタログ

  モジュール間の連携は基本的にすべて `setup.py` の `entry_points`（`invenio_base.apps`, `invenio_base.api_apps`, `invenio_admin.views`, `invenio_celery.tasks`, `flask.commands` 等）を通して行われる。あるモジュールがどこにフックしているか調べる際は、まずそのモジュールの `setup.py` の `entry_points` を確認するとよい。
- `scripts/` — インスタンスのブートストラップ・プロビジョニング・Flask設定（`instance.cfg`）など、上記モジュール群から実際に動作するInvenioインスタンスを構築するための資材が置かれている。
- **依存管理**: **pip** + 仮想環境を使用（`pyproject.toml` は無い）。ルートの `packages.txt`（サードパーティ依存）, `packages-invenio.txt`（Invenio本体）, `requirements-weko-modules.txt`（`modules/` 配下の各パッケージを `-e /code/modules/<name>` で editable install するリスト）, `requirements-devel.txt`（開発・テスト用）を `scripts/create-instance.sh` が順に `pip install` する。
- **環境設定**: 実行環境（サービス構成）は `docker-compose2.yml` で管理（機密情報はコードに直書きしない）。サーバ固有の設定は `scripts/instance.cfg` に記載する（`INVENIO_*` 環境変数を参照するJinjaテンプレート）。

## 開発環境セットアップ / Development Setup
- dockerを利用する。
- リポジトリのクローン後、`install.sh` コマンドを実行すると、`docker-compose2.yml` に定義されたコンテナ群のビルド・初期データ投入・起動までが自動実行される。
- 環境構築後、`https://127.0.0.1/` でサーバにアクセスすることができる。

## テストの実行方法 / Testing
- テストはPostgreSQL/Elasticsearch/Redis/RabbitMQ等の実インフラへの接続を必要とし、それらは `docker-compose2.yml` 内のホスト名（`pgpool`, `elasticsearch`, `redis`, `rabbitmq` 等）でしか解決できない。そのため `docker-compose2.yml` のコンテナ群を起動した状態で、必ず `web` コンテナの中で実行する（ホスト上で直接 `tox`/`pytest` を実行しても接続できず失敗する）。
- テストは基本的にモジュール単位（`modules/<module-name>`）で実行する。CI（`.github/workflows/unit-tests.yml`）も `install.sh` でコンテナを起動した上で、モジュールごとにコンテナ内で以下を実行している。
  ```shell
  docker compose -f docker-compose2.yml exec web bash -c "cd modules/<module-name> && tox"
  ```
- tox を使わず直接pytestで実行する場合も同様にコンテナ内で実行する:
  ```shell
  docker compose -f docker-compose2.yml exec web bash -c "cd modules/<module-name> && .tox/c1/bin/pytest"
  docker compose -f docker-compose2.yml exec web bash -c "cd modules/<module-name> && .tox/c1/bin/pytest tests/test_api.py::test_name"  # 単一テスト
  ```
- 全モジュールをまとめて実行する場合（`modules/invenio-*` と `modules/weko-*` のうち `tests/` を持つもの全て）:
  ```shell
  docker compose -f docker-compose2.yml exec web ./run-tests.sh
  ```
- 各モジュールのテストは `tests/` 配下に置かれ、`conftest.py` が（`pytest-invenio` を利用して）インスタンス全体ではなく最小限のFlaskアプリのfixtureを構築する。`tests/test_examples_app.py`（存在する場合）はそのモジュールの `examples/app.py` デモアプリを対象にしたテスト。
- 新機能を追加した際は必ず対応するテストコードを追加してください
- テストが全てパスすることを確認してから変更を確定します

## コードスタイル / Code Style
※ 現在、CIでの運用停止中。極力これらに従うことを推奨します。
- コーディング規約: **PEP8**に準拠 (スタイルガイドの遵守)
- フォーマッター: **Black** を使用（`black .` でソースコードを整形）
- リンター: **Flake8** を使用（`flake8` で静的解析チェック）
- インポート順の整理: **isort** を使用（`isort .` でインポート並び替え）
- これらのフォーマットチェックはコミット前に必ず実行し、指摘がない状態にしてください
- 各モジュールの `tox.ini` に規約が明記されている: `flake8` は `max-line-length = 119`、`isort` は `black` プロファイルを使用

## セキュリティ方針 / Security
- **秘密情報は厳重に管理**: APIキーやパスワードなど秘密情報は`.env`や環境変数から読み込み、絶対にGitに含めないでください
- **ユーザ入力の検証**: フォームやAPIで受け取る入力はFlaskの仕組み（WTForms、marshmallowによるスキーマ検証等）で適切に検証してください
- **デバッグ設定**: 開発中以外では`DEBUG = False`に設定し、エラーページや機密情報が漏洩しないようにします
- **依存パッケージ**: 新しいパッケージを導入する際はセキュリティ面を確認し、必要に応じてチームの承認を得てください

## プルリクエストガイドライン / PR Guidelines
- **タイトル形式**: `feat: 機能概要` のように、プレフィックスと簡潔な説明を書いてください
- **事前チェック**: コードを提出する前に `flake8` や `pytest` を実行し、エラーやテスト失敗がないことを確認しましょう
- **差分の範囲**: 1つのPRは関連する変更に留め、小さくまとまった変更を心がけてください（大規模な変更は分割を検討）
- **説明コメント**: PRの説明欄には変更内容と目的、動作確認の方法を簡潔に記述してください
