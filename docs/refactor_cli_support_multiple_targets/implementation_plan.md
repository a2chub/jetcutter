# 実装計画書：CLIのマルチターゲット対応リファクタリング

## 目標
`jetdr` CLIをリファクタリングし、DaVinci Resolve以外のエクスポートターゲット（Final Cut Proなど）をサポートするようにする。Factoryパターンを活用し、拡張性の高い構成にする。

## 現状の課題
- `jetdr` CLIの `process` コマンド内に、DaVinci Resolveへのエクスポート処理がハードコードされている。
- Final Cut Pro用の機能 (`jetfcp`) が存在するが、メインの `jetdr` コマンドからは利用できない。
- 新しいエクスポート形式を追加する際に、CLIコードの修正が必要になる。

## 実装方針

### 1. `process` コマンドの汎用化
`src/jetdr/main.py` の `process` コマンドを修正し、特定のエディタへの依存を排除する。

- **引数の追加**: `--target` (エイリアス `-t`) オプションを追加。デフォルトは `davinci`。
- **Factoryの使用**: `jetdr.exporters.create_exporter` を使用して、指定されたターゲットのエクスポーターインスタンスを生成する。
- **インターフェースによる分岐**:
    - `LiveConnectionExporter` (DaVinci等): コンテキストマネージャを使用し、接続状態を確認してエクスポート。
    - `FileExporter` (FCPXML等): 直接エクスポートメソッドを呼び出し。

### 2. `batch` コマンドの追従
`batch` コマンドも同様に `--target` オプションを受け取り、内部で呼び出す `process` コマンドに渡すように修正する。

## 影響範囲
- `src/jetdr/main.py`
- 既存の `jetfcp` コマンドには影響しない（共存可能）。

## 検証計画
- CLIヘルプの表示確認
- コードの静的解析（構文チェック）
