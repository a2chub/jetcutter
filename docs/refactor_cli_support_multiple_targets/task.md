# タスクリスト：CLIのマルチターゲット対応リファクタリング

## 概要
`jetdr` CLIコマンドを拡張し、DaVinci ResolveだけでなくFinal Cut Proなどの他のエクスポートターゲットもサポートするようにリファクタリングする。

## タスク
- [x] `src/jetdr/main.py` の `process` コマンドを修正
    - [x] `--target` オプションの追加
    - [x] `ExporterRegistry` と `create_exporter` を使用した動的なエクスポーター生成の実装
    - [x] `LiveConnectionExporter` と `FileExporter` の分岐処理の実装
- [x] `src/jetdr/main.py` の `batch` コマンドを修正
    - [x] `--target` オプションの追加
    - [x] `process` コマンド呼び出し時に `target` 引数を渡すように修正
- [x] 動作確認
    - [x] `jetdr process --help` でオプションが表示されるか確認
    - [x] リファクタリング後のコードが構文的に正しいか確認
