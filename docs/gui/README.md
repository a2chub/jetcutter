# JetCutter GUI

macOS向けのグラフィカルユーザーインターフェース。

## インストール

### 開発環境

```bash
# GUI依存関係をインストール
uv pip install -e ".[gui]"

# 起動
uv run python -m jetcutter.gui.app
```

### スタンドアロンアプリ

```bash
# py2appをインストール
pip install py2app

# .appバンドルをビルド
python setup_gui.py py2app

# 実行
open dist/JetCutter.app
```

## 機能

### 処理タブ

- 動画ファイルの選択（.mp4, .mov, .avi, .mkv, .webm対応）
- エクスポート先の選択（Final Cut Pro / DaVinci Resolve）
- タイムライン名と出力先の設定
- 処理の開始/キャンセル

### 設定タブ

| セクション | パラメータ | 説明 |
|------------|------------|------|
| 無音検知 | しきい値 (dB) | 無音と判定する音量レベル（デフォルト: -40dB） |
| 無音検知 | 最小無音時間 (ms) | カット対象とする最小の無音期間（デフォルト: 300ms） |
| フィラー検知 | モデル | Whisperモデルサイズ（tiny〜large-v3） |
| フィラー検知 | 言語 | 認識対象言語 |
| フィラー検知 | デバイス | 使用デバイス（auto/cuda/cpu） |
| マージン | 前/後マージン (ms) | 保持区間の前後に追加するバッファ |
| 一般 | FPS | タイムラインのフレームレート |
| 一般 | 最小保持時間 (ms) | 保持する最短区間 |

### 結果タブ

- 処理結果のサマリー（総時間、削減時間、削減率）
- 検出したセグメントの一覧表示
- セグメント種別（無音/フィラー/保持）でのフィルタリング

## 必要要件

- macOS 10.15以降
- Python 3.10以上
- ffmpeg（Homebrew: `brew install ffmpeg`）

## 注意事項

### Whisperモデルのダウンロード

初回起動時に、選択したWhisperモデルがダウンロードされます。
モデルサイズによっては1GB以上のダウンロードが発生します。

| モデル | サイズ | 精度 |
|--------|--------|------|
| tiny | ~75MB | 低 |
| base | ~150MB | 中低 |
| small | ~500MB | 中 |
| medium | ~1.5GB | 中高 |
| large-v3 | ~3GB | 高 |

### DaVinci Resolve連携

DaVinci Resolve連携を使用する場合は、DaVinci Resolve Studio（有償版）が必要です。
無償版にはスクリプティングAPIが含まれていません。

## トラブルシューティング

### ffmpegが見つからない

```bash
# Homebrewでインストール
brew install ffmpeg
```

### PySimpleGUI4がインストールできない

```bash
# pipで直接インストール
pip install PySimpleGUI4
```

### py2appビルドが失敗する

```bash
# クリーンビルド
rm -rf build dist
python setup_gui.py py2app
```
