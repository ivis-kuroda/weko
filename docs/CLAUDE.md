返答は全て日本語で行うこと

## ドキュメントディレクトリ構成

エージェントが設計書・規約を正確に参照するためのディレクトリ構成。各パイプライン共通。

```
/weko/
├── docs/
│   ├── agent/                          ← エージェント向けパイプライン・ルール文書
│   │   ├── ai_implementation_pipeline.md ← 実装支援パイプライン
│   │   ├── ai_test_pipeline.md          ← テスト自動化パイプライン
│   │   └── detailed_design_split_rules.md ← 詳細設計書分割ルール
│   ├── conventions/                    ← プロジェクト共通の規約・設計書テンプレート（不変）
│   │   ├── コーディング規約Ver.1.4.xlsx ← コーディング規約
│   │   └── デザインガイドライン.docx    ← デザイン規約・ガイドライン
│   └── cases/                          ← 案件ごとに分離
│       └── <案件名>/
│           ├── basic_design.md              ← 基本設計書
│           ├── detailed_design.md           ← 詳細設計書（全機能まとめ版・分割元）
│           ├── detailed_design_01_<機能名>.md ← 詳細設計書（分割版・実装単位ごと）
│           ├── detailed_design_02_<機能名>.md ← 詳細設計書（分割版・実装単位ごと）
│           ├── ui_design.xlsx               ← 画面設計書（Excel）
│           ├── implementation_review.md     ← 実装レビュー記録表
│           └── notes.md                    ← 案件固有のメモ・補足
└── (既存ファイル)
```

### ディレクトリの役割

| ディレクトリ | 内容 | 参照エージェント | 更新頻度 |
|-------------|------|-----------------|---------|
| `docs/agent/` | パイプライン定義・分割ルールなどエージェント向け手順書 | 全エージェント | 低 |
| `docs/conventions/` | プロジェクト共通の規約 | 全エージェント | 低 |
| `docs/cases/<案件名>/` | 案件固有の設計書 | 当該案件の実装・テストパイプライン | 高 |

### 設計書の配置ルール

- 基本設計書・詳細設計書は Markdown (`.md`) 形式で配置
- 画面設計書は Excel (`.xlsx`) 形式で配置
- 案件名の命名は `YYYYMMDD-短縮名` 形式（例: `202604-swordv3-links`）
- 実装レビュー記録表は `implementation_review.md` として案件ディレクトリに配置する。実装コード生成完了後にエージェントが雛形を生成し、人間がレビュー内容を記入する
- 詳細設計書の分割版は `detailed_design_NN_<機能名>.md`（NN は 01 から始まる2桁の連番）形式で配置する。分割元の `detailed_design.md` は削除せず残す

## AIエージェントによる実装支援パイプライン

詳細は [docs/agent/ai_implementation_pipeline.md](docs/agent/ai_implementation_pipeline.md) を参照。

---

## AIエージェントによるテスト自動化パイプライン

詳細は [docs/agent/ai_test_pipeline.md](docs/agent/ai_test_pipeline.md) を参照。

---

## 詳細設計書の分割ルール

詳細は [docs/agent/detailed_design_split_rules.md](docs/agent/detailed_design_split_rules.md) を参照。

## オーケストレーターの行動原則

- オーケストレーター自身はコード生成・ファイル編集・設計書読込などの作業を直接行わない
- すべての作業はサブエージェントに委譲する
- オーケストレーターの役割は「判断・指示・進捗管理」のみ
