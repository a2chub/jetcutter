# JetCutter 開発ガイド

このドキュメントは、JetCutterの開発ワークフローとベストプラクティスを説明します。

## ブランチ戦略

JetCutterは以下のブランチ構造を採用しています：

```
dev (安定版メインブランチ)
 └── v{X.Y}-rc (リリース候補ブランチ)
      ├── feature-xxx (機能A)
      ├── feature-yyy (機能B)
      └── feature-zzz (機能C)
```

### ブランチの役割

| ブランチ | 役割 | マージ先 |
|---------|------|----------|
| `dev` | 安定版メインブランチ。リリース済みコードを保持 | - |
| `v{X.Y}-rc` | リリース候補統合ブランチ。複数機能を統合してテスト | → dev (リリース時) |
| `feature-*` | 個別機能開発ブランチ | → v{X.Y}-rc |
| `fix-*` | バグ修正ブランチ | → dev または v{X.Y}-rc |
| `refactor-*` | リファクタリングブランチ | → dev または v{X.Y}-rc |

## 開発ワークフロー

### 1. 新規リリースの開始

リリース候補ブランチを作成：

```bash
git checkout dev
git pull origin dev
git checkout -b v1.5-rc
git push -u origin v1.5-rc
```

### 2. 機能開発

リリース候補ブランチから機能ブランチを作成：

```bash
git checkout v1.5-rc
git checkout -b feature-<機能名>
# 開発作業
git push -u origin feature-<機能名>
```

### 3. 機能のマージ

機能完成後、リリース候補ブランチにマージ：

```bash
git checkout v1.5-rc
git merge feature-<機能名>
git push origin v1.5-rc
# 不要になったブランチを削除
git branch -d feature-<機能名>
git push origin --delete feature-<機能名>
```

### 4. リリース

全機能統合後、devブランチにマージしてリリース：

```bash
git checkout dev
git merge v1.5-rc
git push origin dev
git tag v1.5.0
git push origin v1.5.0
```

## バージョン更新手順

バージョン番号は以下の3箇所で管理されています。更新時は全て同期してください：

| ファイル | 場所 | 例 |
|---------|------|-----|
| `pyproject.toml` | `[project].version` | `"1.5.0-rc.1"` |
| `pyproject.toml` | `[tool.briefcase].version` | `"1.5.0"` |
| `src/jetcutter/__init__.py` | `__version__` | `"1.5.0-rc.1"` |

**注意**: Briefcaseはプレリリースサフィックス（-rc.1等）を含めないでください。

### バージョン形式

[Semantic Versioning 2.0.0](https://semver.org/)に準拠：

```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

プレリリース版：
- `1.5.0-alpha.1` - 初期開発版
- `1.5.0-beta.1` - 機能完成版
- `1.5.0-rc.1` - リリース候補

## CHANGELOG更新ルール

[Keep a Changelog 1.1.0](https://keepachangelog.com/ja/1.1.0/)形式を採用。

### 開発中の記録

`[Unreleased]`セクションに変更を追記：

```markdown
## [Unreleased]

### Added
- 新機能の説明

### Changed
- 変更点の説明

### Fixed
- 修正内容の説明
```

### リリース時の整形

```markdown
## [1.5.0] - 2026-01-15

### Added
- 新機能の説明
```

## 品質チェックリスト

リリース前に以下を確認：

### テスト

```bash
# 全テスト実行
pytest

# カバレッジレポート付き
pytest --cov=src/jetcutter --cov-report=html
```

### Lint・フォーマット

```bash
# Lint
ruff check src/

# フォーマット確認
ruff format src/ --check

# 型チェック
mypy src/
```

### ビルド確認

```bash
# Briefcaseアプリ更新・ビルド
uv run briefcase update macOS app
uv run briefcase build macOS app

# DMGパッケージ作成
uv run briefcase package macOS app --adhoc-sign
```

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/)形式を使用：

| プレフィックス | 用途 | 例 |
|---------------|------|-----|
| `feat:` | 新機能 | `feat: add batch export support` |
| `fix:` | バグ修正 | `fix: resolve memory leak in audio processing` |
| `docs:` | ドキュメント | `docs: update installation guide` |
| `test:` | テスト | `test: add unit tests for segment merger` |
| `refactor:` | リファクタリング | `refactor: simplify exporter factory` |
| `chore:` | その他 | `chore: release v1.5.0` |

## 開発環境セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/a2chub/jetcutter.git
cd jetcutter

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate

# 開発依存関係のインストール
uv pip install -e ".[dev]"
```

## 関連ドキュメント

- [VERSIONING.md](./VERSIONING.md) - バージョニング方針
- [CHANGELOG.md](/CHANGELOG.md) - 変更履歴
- [CLAUDE.md](/CLAUDE.md) - AI開発ガイド・ベストプラクティス
- [docs/releases/](./releases/) - リリースノート
