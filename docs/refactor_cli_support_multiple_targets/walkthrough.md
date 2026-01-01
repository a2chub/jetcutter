# 修正内容の確認 (Walkthrough)

## 概要
`jetdr` CLI の `process` および `batch` コマンドをリファクタリングし、`--target` オプションによってエクスポート先（DaVinci Resolve, Final Cut Pro等）を切り替えられるようにしました。

## 変更ファイル
`src/jetdr/main.py`

## 主な変更点

### 1. `process` コマンドの更新

DaVinci Resolve への依存を削除し、`ExporterRegistry` を使用した汎用的な実装に変更しました。

```python
@app.command()
def process(
    # ... 既存の引数 ...
    target: str = typer.Option(
        "davinci",
        "--target",
        "-t",
        help="ターゲットエディタ (davinci, fcp)",
    ),
    # ...
):
    # ... インポートの更新 ...
    from jetdr.exporters import (
        ExportConfig,
        LiveConnectionExporter,
        create_exporter,
    )

    # ... (中略) ...

    # エクスポート処理の分岐
    if not dry_run:
        task = progress.add_task(f"Exporting to {target}...", total=None)
        try:
            exporter = create_exporter(target)
            
            export_config = ExportConfig(
                video_path=video_path,
                output_name=output_name,
                fps=config.fps,
                metadata={"output_path": str(output_path)} if output_path else {}
            )

            result = None
            
            if isinstance(exporter, LiveConnectionExporter):
                with exporter:
                    if exporter.is_connected:
                        result = exporter.export(keep_segments, export_config)
                    # ...
            else:
                result = exporter.export(keep_segments, export_config)
            
            # ... 結果表示 ...
```

### 2. `batch` コマンドの更新

`target` オプションを追加し、`process` コマンドへの受け渡しを追加しました。

```python
@app.command()
def batch(
    # ...
    target: str = typer.Option(
        "davinci",
        "--target",
        "-t",
        help="ターゲットエディタ (davinci, fcp)",
    ),
    # ...
):
    # ...
    # processコマンド呼び出し時に引数を追加
    process(
        video_path=video,
        output_name=f"JetCut_{video.stem}",
        target=target,  # 追加
        config_path=config_path,
        dry_run=False,
        verbose=False,
    )
```

## 結果
これにより、ユーザーは以下のようにコマンドを実行してターゲットを指定できるようになりました。

```bash
# DaVinci Resolve (デフォルト)
jetdr process video.mp4

# Final Cut Pro
jetdr process video.mp4 --target fcp
```
