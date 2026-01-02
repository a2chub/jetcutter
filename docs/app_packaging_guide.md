# JetCutter macOSアプリパッケージング ガイド

**作成日**: 2026-01-02
**対象**: PyObjC + AppKitベースのJetCutterアプリケーション

## 調査概要

JetCutterアプリケーションを.appパッケージとして配布するための、2024-2025年における最新のパッケージングツールを調査しました。

## 推奨ツール: **Briefcase (BeeWare)**

### 選定理由

1. **PyObjC + AppKitとの最高の互換性**
   - macOSネイティブのXcodeプロジェクト構造をテンプレートとして使用
   - AppKitとの親和性が極めて高い
   - PyObjC Delegateパターンの問題が発生しにくい

2. **現代的な開発体験**
   - `pyproject.toml` で完結する設定
   - `setup.py` 等のレガシーファイル不要
   - Python 3.12/3.13への対応が早い

3. **コード署名・公証の自動化**
   - `briefcase publish macos` コマンド一つで署名から公証まで実行可能
   - 開発者の手作業を最小化

4. **Apple Siliconへの最適化**
   - M1/M2/M3チップへの対応が進んでいる
   - Universal Buildサポート（Intel + Apple Silicon両対応）

## ツール比較表

| 比較項目 | Briefcase | PyInstaller | py2app |
|:---|:---|:---|:---|
| **PyObjC互換性** | ★★★★★ | ★★★★☆ | ★★★★★ |
| **セットアップ** | pyproject.toml | CLIまたはSpecファイル | setup.py (レガシー) |
| **依存関係解決** | 標準的 | ★★★★★ 強力 | ★☆☆☆☆ 脆弱 |
| **バイナリ同梱** | 容易 | 容易 | 手動設定多い |
| **署名・公証** | ★★★★★ 標準機能 | フック経由で対応可 | 手動スクリプト必要 |
| **アプリサイズ** | 中 | 中〜大 | 最小 |
| **コミュニティ** | 非常に活発 | 最大・安定 | 停滞気味 |
| **2025年の推奨度** | ★★★★★ | ★★★★☆ | ★★☆☆☆ |

### 補足

- **PyInstaller**: 複雑なバイナリ依存関係（faster-whisper/ctranslate2等）の解決力は随一。Briefcaseで問題が発生した場合の代替案として有力
- **py2app**: PyObjC開発元が作成しているが、メンテナンスが停滞。現代的なPythonパッケージへの対応が遅れている

---

## Briefcaseセットアップ手順

### 1. pyproject.toml設定

現在の`pyproject.toml`に以下のセクションを追加:

```toml
[tool.briefcase]
project_name = "JetCutter"
bundle = "com.yourcompany"  # 変更必要: 実際のバンドルIDに
version = "0.1.0"
url = "https://github.com/yourusername/jetcutter"  # 変更必要
author = "Your Name"  # 変更必要
author_email = "your@email.com"  # 変更必要

[tool.briefcase.app.jetcutter]
formal_name = "JetCutter"
description = "AI Video Editor - 無音・フィラー自動検知ツール"

# 依存関係（既存のdependenciesから引用 + GUI系追加）
requires = [
    "ffmpeg-python>=0.2.0",
    "pydub>=0.25.1",
    "faster-whisper>=1.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "loguru>=0.7.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pyobjc-core>=10.0",
    "pyobjc-framework-Cocoa>=10.0",
]

sources = ["src/jetcutter"]

# macOS固有設定
[tool.briefcase.app.jetcutter.macOS]
universal_build = true  # Intel + Apple Silicon両対応
requires = [
    "std-nslog>=1.0.0",  # ログ出力のためのBriefcase推奨パッケージ
]

# Info.plist設定
info = {
    "NSHighResolutionCapable" = true,
    "LSMinimumSystemVersion" = "11.0",
    "CFBundleIdentifier" = "com.yourcompany.jetcutter",  # bundle と同じ値
}
```

### 2. Briefcaseのインストールと初期化

```bash
# Briefcaseインストール
uv pip install briefcase

# プロジェクト初期化（既存のpyproject.tomlから設定を読み込む）
briefcase create macOS

# アプリケーションをビルド
briefcase build macOS

# 開発モードで実行（Ad-hoc署名で起動確認）
briefcase dev macOS
```

### 3. ffmpegバイナリの同梱

JetCutterは外部の`ffmpeg`バイナリに依存しているため、アプリ内に同梱する必要があります。

#### 方法1: Homebrewからコピー（開発用）

```bash
# ffmpegのパスを確認
which ffmpeg  # 例: /opt/homebrew/bin/ffmpeg

# プロジェクトにコピー
mkdir -p resources
cp /opt/homebrew/bin/ffmpeg resources/
```

#### 方法2: 公式ビルドをダウンロード（配布用）

```bash
# Intel + Apple Silicon用のユニバーサルバイナリを取得
# https://evermeet.cx/ffmpeg/ から最新版をダウンロード
mkdir -p resources
# ダウンロードしたffmpegをresourcesに配置
```

#### pyproject.tomlに追加

```toml
[tool.briefcase.app.jetcutter.macOS]
# 既存の設定...

# ffmpegバイナリをContents/Resourcesに配置
resources = [
    "resources/ffmpeg",
]
```

#### アプリケーションコードでの参照

`src/jetcutter/audio/extractor.py` 等でffmpegパスを解決する処理を追加:

```python
import sys
import os

def get_ffmpeg_path() -> str:
    """
    実行環境に応じたffmpegのパスを返す

    Returns:
        ffmpegバイナリのパス
    """
    if getattr(sys, 'frozen', False):
        # Briefcaseでパッケージ化された場合
        # .app/Contents/Resources/ffmpeg に配置されている
        if sys.platform == 'darwin':
            bundle_dir = os.path.dirname(sys.executable)
            # Contents/MacOS から Contents/Resources へ
            resources_dir = os.path.join(os.path.dirname(bundle_dir), 'Resources')
            ffmpeg_path = os.path.join(resources_dir, 'ffmpeg')
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path

    # 開発環境 or システムのffmpegを使用
    return 'ffmpeg'

# pydubでの使用例
from pydub import AudioSegment
AudioSegment.converter = get_ffmpeg_path()
```

---

## コード署名と公証（Notarization）

### 必要な前提条件

1. **Apple Developer Program**への加入（年間99ドル）
2. **Developer ID Application証明書**の取得
3. **App-Specific Password**の生成

### Entitlementsファイルの作成

PyObjC + Pythonアプリには動的コード実行の許可が必要です。

`entitlements.plist` をプロジェクトルートに作成:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Python動的インポートのため -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- Python拡張モジュール(.so)のため -->
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>

    <!-- JITコンパイル（必要に応じて） -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
</dict>
</plist>
```

### 署名とパッケージング

```bash
# 1. アプリをビルド
briefcase build macOS

# 2. パッケージング（.app → .dmg作成）
briefcase package macOS \
    --adhoc-sign  # 開発時はAd-hoc署名

# 本番配布用（Developer ID証明書使用）
briefcase package macOS \
    --identity "Developer ID Application: Your Name (TEAMID)"
```

### 公証プロセス

```bash
# 1. .appを.dmgまたは.zipにパッケージ（Briefcaseが自動実行）

# 2. Appleに公証申請
xcrun notarytool submit macOS/JetCutter-0.1.0.dmg \
    --apple-id "your-email@example.com" \
    --password "app-specific-password" \
    --team-id "YOUR_TEAM_ID" \
    --wait

# 3. 公証成功後、チケットをStaple（オフライン起動の高速化）
xcrun stapler staple macOS/JetCutter-0.1.0.dmg
```

### Briefcaseの自動公証機能

Briefcaseは公証プロセスも自動化できます:

```bash
briefcase publish macOS \
    --identity "Developer ID Application: Your Name (TEAMID)" \
    --notarize \
    --notarize-apple-id "your-email@example.com" \
    --notarize-password "app-specific-password" \
    --notarize-team-id "YOUR_TEAM_ID"
```

---

## PyInstallerを使う場合（代替案）

faster-whisper等の複雑なバイナリ依存関係で問題が発生した場合の代替手段。

### PyInstaller Specファイル例

`jetcutter.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

block_cipher = None

# faster-whisper/ctranslate2の共有ライブラリ収集
binaries = collect_dynamic_libs('ctranslate2')
binaries += collect_dynamic_libs('faster_whisper')

# ffmpegバイナリ
ffmpeg_bin = ('resources/ffmpeg', '.')

# データファイル
datas = collect_data_files('faster_whisper')
datas += [('config/*.yaml', 'config')]

a = Analysis(
    ['src/jetcutter/gui/app.py'],
    pathex=[],
    binaries=binaries + [ffmpeg_bin],
    datas=datas,
    hiddenimports=[
        'pydantic_core._pydantic_core',
        'pyobjc-framework-AppKit',
        'AppKit',
        'Foundation',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JetCutter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリ
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='universal2',  # Intel + Apple Silicon
    codesign_identity=None,  # 本番では証明書IDを指定
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JetCutter',
)

app = BUNDLE(
    coll,
    name='JetCutter.app',
    icon=None,  # アイコンファイルがあれば指定
    bundle_identifier='com.yourcompany.jetcutter',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '11.0',
        'NSPrincipalClass': 'NSApplication',
    },
)
```

### ビルドと署名

```bash
# 1. PyInstallerインストール
uv pip install pyinstaller

# 2. ビルド
pyinstaller jetcutter.spec

# 3. 署名（Entitlementsファイル使用）
codesign --sign "Developer ID Application: Your Name (TEAMID)" \
         --options runtime \
         --entitlements entitlements.plist \
         --deep --force \
         dist/JetCutter.app

# 4. 検証
codesign -vvv --deep --strict dist/JetCutter.app
spctl -a -vv dist/JetCutter.app
```

---

## 開発中のGatekeeper回避

開発時に「開発元を検証できない」エラーが出る場合:

```bash
# Quarantine属性を削除
xattr -cr /path/to/JetCutter.app

# Ad-hoc署名（証明書なし）
codesign --force --deep -s - JetCutter.app
```

または、システム設定から手動で許可:
1. アプリを起動しようとする
2. 「システム設定 > プライバシーとセキュリティ」を開く
3. 下部の「このまま開く」をクリック

---

## よくある問題と対処法

### 1. PyObjC Delegateメソッドが呼ばれない

**原因**: Delegateオブジェクトがガベージコレクション(GC)で解放されている

**対処法**: Delegateオブジェクトを必ずクラスのインスタンス変数として保持

```python
# ❌ 悪い例
window.setDelegate_(MyDelegate.alloc().init())

# ✅ 良い例
self.my_delegate = MyDelegate.alloc().init()
window.setDelegate_(self.my_delegate)
```

### 2. faster-whisperのインポートエラー

**原因**: ctranslate2の共有ライブラリ(.dylib)が正しく収集されていない

**対処法**: PyInstallerの`collect_dynamic_libs`を使用するか、手動で`--add-binary`で追加

### 3. ffmpegが見つからない

**原因**: パッケージ化されたアプリ内でffmpegのパスが正しく解決されていない

**対処法**: `sys.frozen`フラグで実行環境を判定し、適切なパスを返す関数を実装（上記参照）

### 4. 処理中に新しいアプリウィンドウが起動する

**原因**: `multiprocessing.set_start_method("spawn")` を使用している場合、faster-whisper/ctranslate2が内部でマルチプロセスを起動する際に、`spawn`方式では完全に新しいPythonインタプリタが起動され、アプリ全体が再実行される

**対処法**: macOSでは`fork`方式を使用し、スレッド数を制限する環境変数を設定

```python
# src/jetcutter/__main__.py
import multiprocessing
import os
import sys

def run():
    """アプリケーションを起動"""
    multiprocessing.freeze_support()

    # マルチスレッド数を制限（ctranslate2/faster-whisper対策）
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    # macOSでは fork を使用（spawn はアプリ再起動を引き起こす）
    if sys.platform == "darwin":
        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError:
            pass  # 既に設定済みの場合はスキップ

    from jetcutter.gui.app import main
    main()

if __name__ == "__main__":
    run()
```

**技術的詳細**:
- `spawn`: 完全な新しいPythonインタプリタを起動 → パッケージ化アプリではアプリ全体が再実行される
- `fork`: 親プロセスのメモリをコピー → アプリは再実行されない
- `OMP_NUM_THREADS=1`: OpenMPの並列スレッド数を制限（ctranslate2が使用）
- `MKL_NUM_THREADS=1`: Intel MKLの並列スレッド数を制限

### 5. 公証が失敗する（Notarization rejected）

**よくある原因**:
- Hardened Runtimeが有効でない → `--options runtime`フラグ必須
- 再帰的署名の不備 → `--deep`フラグ使用
- タイムスタンプの欠如 → `--timestamp`フラグ追加

**確認方法**:
```bash
# ログを確認
xcrun notarytool log <submission-id> \
    --apple-id "your-email@example.com" \
    --password "app-specific-password" \
    --team-id "YOUR_TEAM_ID"
```

---

## 推奨される開発フロー

### フェーズ1: 開発環境（Ad-hoc署名）

```bash
# 1. Briefcaseでアプリ作成
briefcase create macOS

# 2. 開発モードで実行
briefcase dev macOS

# 3. ビルドとテスト
briefcase build macOS
briefcase run macOS
```

### フェーズ2: テスト配布（開発者証明書）

```bash
# Developer ID証明書で署名
briefcase package macOS \
    --identity "Developer ID Application: Your Name (TEAMID)"

# 生成された.dmgをテスターに配布
```

### フェーズ3: 本番配布（公証済み）

```bash
# 署名 + 公証 + Staple を一括実行
briefcase publish macOS \
    --identity "Developer ID Application: Your Name (TEAMID)" \
    --notarize \
    --notarize-apple-id "your-email@example.com" \
    --notarize-password "app-specific-password" \
    --notarize-team-id "YOUR_TEAM_ID"
```

---

## まとめ

### JetCutterに最適なツール: **Briefcase**

**理由**:
1. PyObjC + AppKitとの最高の互換性
2. 現代的な`pyproject.toml`ベース設定
3. 署名・公証プロセスの自動化
4. Apple Siliconへの最適化

**代替案**: 複雑なバイナリ依存関係で問題が発生した場合は**PyInstaller**を検討

**非推奨**: py2app（メンテナンス停滞のため）

### 次のステップ

1. `pyproject.toml`にBriefcase設定を追加
2. ffmpegバイナリを`resources/`に配置
3. `briefcase create macOS`で初期プロジェクト作成
4. 開発モードでテスト実行
5. 本番配布前にApple Developer Programに加入し証明書取得

### 参考リンク

- [Briefcase公式ドキュメント](https://briefcase.readthedocs.io/)
- [PyInstaller公式ドキュメント](https://pyinstaller.org/)
- [Apple公証ガイド](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [ffmpeg macOSビルド](https://evermeet.cx/ffmpeg/)
