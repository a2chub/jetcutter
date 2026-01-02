# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-01-02

### Removed

- **レガシーGUIコード削除** - `src/jetcutter/gui_legacy/` を完全削除（約2,151行）
  - PySimpleGUI4ベースの旧GUI実装
  - 関連するハンドラ、コンスタント、処理コード
- **PySimpleGUI4依存関係** - pyproject.tomlから削除
- **py2app設定ファイル** - `setup_gui.py` を削除（Briefcaseに統一）
- **不要なライセンスファイル** - `LICENSES/LGPL-3.0.txt`, `LICENSES/GPL-3.0.txt`

### Changed

- 全依存関係がMITライセンスに統一
- ドキュメント更新（PySimpleGUI4参照を削除）
- GUI開発手順をBriefcaseに統一

## [1.1.0] - 2026-01-02

### Added

- **Aboutダイアログ** - アプリケーションメニューにAbout JetCutterを追加
  - バージョン情報表示
  - ライセンス情報表示
  - GitHubリポジトリへのリンク
- **ライセンスコンプライアンス対応** - DMG配布に必要なライセンス文書を整備
  - `LICENSES/` フォルダにMIT全文を追加
  - `THIRD_PARTY_LICENSES.md` で全依存パッケージの帰属表示を記載

### Changed

- pyproject.tomlのBriefcase設定でライセンスファイルをバンドルに含めるよう更新

## [1.0.0] - 2026-01-02

### Added

- **macOS ネイティブGUI** - PyObjC + AppKitによるネイティブmacOSアプリケーション
  - 3タブ構成（処理・設定・結果）
  - リアルタイム進捗表示
  - 処理時間表示（MM:SS.SS形式）
- **Final Cut Pro対応** - FCPXML v1.10形式でのタイムライン出力
  - DTD完全準拠
  - DJIドローン等の非標準タイムコード対応
  - 自動FPS検出
- **DaVinci Resolve対応** - Scripting APIによる直接連携（Studio版必須）
- **無音区間自動検知** - pydubによる音量ベースの無音検知
  - しきい値設定可能（デフォルト: -40dB）
  - 最小無音時間設定可能（デフォルト: 300ms）
- **フィラー自動検知** - faster-whisperによるAI音声認識
  - 日本語フィラー対応（「あー」「えっと」「まあ」等）
  - カスタム辞書対応
  - GPU/CPU自動選択
- **CLIツール** - typerによるコマンドラインインターフェース
  - `jetcutter gui` - GUIアプリ起動
  - `jetcutter process` - 動画処理
  - `jetcutter analyze` - 解析のみ
  - `jetcutter export` - FCPXML出力
  - `jetcutter validate` - FCPXML検証
- **Briefcaseパッケージング** - macOS .appバンドル生成対応
- **ランディングページ** - GitHub Pages対応のプロダクトサイト

### Fixed

- タブ切り替え問題（SettingsTabControllerに@propertyデコレータが欠落）
- マルチプロセス新規ウィンドウ問題（multiprocessing開始方式をspawn→forkに変更）
- FCPXML 1.10 DTD準拠修正（media-rep要素使用、format name属性必須）
- GUIデッドロック問題（threading.Lock→RLockに変更）

### Security

- ffmpegバイナリのパス解決をバンドル版とシステム版で分離

---

[Unreleased]: https://github.com/a2chub/jetcutter/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/a2chub/jetcutter/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/a2chub/jetcutter/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/a2chub/jetcutter/releases/tag/v1.0.0
