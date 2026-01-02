# バージョニング方針

JetCutterは[Semantic Versioning 2.0.0](https://semver.org/lang/ja/)に準拠したバージョン管理を採用しています。

## バージョン形式

```
MAJOR.MINOR.PATCH
```

| 要素 | 意味 | 変更時の例 |
|------|------|-----------|
| **MAJOR** | 後方互換性のない変更 | APIの破壊的変更、CLI引数の変更 |
| **MINOR** | 後方互換性を保った機能追加 | 新しい検知アルゴリズム、新規出力形式 |
| **PATCH** | 後方互換性を保ったバグ修正 | 検知精度の改善、UI修正 |

## プレリリース版

正式リリース前のバージョンには以下のサフィックスを付与します：

```
1.1.0-alpha.1   # 初期開発版（不安定）
1.1.0-beta.1    # 機能完成版（テスト中）
1.1.0-rc.1      # リリース候補（最終確認中）
```

## バージョン管理場所

バージョンは以下のファイルで一元管理されています：

| ファイル | 場所 | 用途 |
|---------|------|------|
| `pyproject.toml` | `[project].version` | PyPI / pip |
| `pyproject.toml` | `[tool.briefcase].version` | macOS .appバンドル |

**重要**: バージョン更新時は両方の値を同期してください。

## リリースプロセス

### 1. リリースブランチの作成

```bash
git checkout dev
git pull origin dev
git checkout -b release/vX.Y.Z
```

### 2. バージョン番号の更新

`pyproject.toml`の2箇所を更新：
- `[project]` セクションの `version`
- `[tool.briefcase]` セクションの `version`

### 3. CHANGELOG.mdの更新

`[Unreleased]`セクションの内容を新しいバージョンセクションに移動：

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- 新機能の説明

### Changed
- 変更点の説明

### Fixed
- 修正内容の説明
```

### 4. リリースノートの作成

`docs/releases/vX.Y.Z.md`を作成し、詳細なリリース情報を記載。

### 5. コミットとマージ

```bash
git add .
git commit -m "chore: release vX.Y.Z"
git checkout dev
git merge release/vX.Y.Z
git push origin dev
```

### 6. タグの作成とプッシュ

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

### 7. GitHub Releaseの作成

GitHubでタグからReleaseを作成し、リリースノートを添付。

## 変更履歴の記録規則

[Keep a Changelog 1.1.0](https://keepachangelog.com/ja/1.1.0/)形式を採用：

| カテゴリ | 説明 |
|---------|------|
| `Added` | 新機能 |
| `Changed` | 既存機能の変更 |
| `Deprecated` | 将来削除予定の機能 |
| `Removed` | 削除された機能 |
| `Fixed` | バグ修正 |
| `Security` | セキュリティ修正 |

## 関連ドキュメント

- [CHANGELOG.md](/CHANGELOG.md) - 変更履歴
- [docs/releases/](./releases/) - 各バージョンのリリースノート
