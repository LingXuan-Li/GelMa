# TVオーバースキャン対策対応 Webビューワ(GelMa) 開発仕様書

## 概要

Python製のTV向けWebビューワアプリを開発する。

主目的は：

* 古いテレビのオーバースキャン対策
* HDMI接続時の安全表示
* kiosk / サイネージ用途
* Raspberry Pi / Windows対応

である。

通常のWebブラウザではなく、

「TVへ安全にWeb表示する専用ブラウザ」

として設計する。

---

# 開発方針

## 最重要目標

以下を優先する：

1. 古いテレビでもUIが見切れない
2. 操作UIをTV側へ極力表示しない
3. セカンドスクリーンへ自動表示
4. 簡単に調整できる
5. 安定動作

---

# 推奨技術構成

## GUI

* Python
* PyQt6
* QtWebEngine

## 対応OS

* Windows
* Linux
* Raspberry Pi OS

---

# 基本構成

アプリは2ウィンドウ構成とする。

```text
ControlWindow（操作画面）
DisplayWindow（TV表示画面）
```

---

# 1. ControlWindow（操作画面）

## 役割

* 通常ブラウザ機能
* URL入力
* HOME画面
* 各種設定
* TV表示制御

## 特徴

* 通常ウィンドウ
* フルスクリーンではない
* PC側で操作する

---

# 2. DisplayWindow（TV表示画面）

## 役割

* TV専用表示
* フルスクリーン表示
* オーバースキャン対策
* kiosk表示

## 特徴

* UI最小
* タイトルバー無し
* Frameless
* フルスクリーン固定

---

# 重要仕様

## セカンドスクリーン自動検出

起動時に：

```python
QApplication.screens()
```

を使用し画面一覧を取得する。

---

## 動作ルール

### 画面数が2以上の場合

* ControlWindow
  → メイン画面

* DisplayWindow
  → セカンドスクリーン

へ自動配置。

DisplayWindowは：

```python
showFullScreen()
```

で表示する。

---

## 画面数が1の場合（重要）

### フルスクリーン機能を無効化する

理由：

* 操作不能防止
* kiosk誤動作防止
* UI喪失防止

この場合：

* DisplayWindowを使用しない
* ControlWindowのみ動作
* 通常ブラウザモードとして動作

---

# Web表示機能

## 必須

* URL表示
* HTTPS対応
* HTML/CSS/JavaScript対応
* リロード
* ナビゲーション

---

# HOME機能

## HOME画面を実装

起動時にHOMEを表示する。

---

## HOME内容

* YouTube
* Google
* Dashboard
* Signage
* Custom URL

などをタイル表示する。

---

## HOME設計

重要UIは：

```css
padding: 5vw;
```

程度のSafe Areaを確保する。

---

# オーバースキャン対策

## 必須機能

* 表示縮小
* Safe Margin
* 内側表示

---

# 実装方式

DisplayWindow内で：

```python
layout.setContentsMargins(
    left,
    top,
    right,
    bottom
)
```

を使用。

さらに：

```python
webview.setZoomFactor(scale)
```

を併用。

---

# ズーム機能

## ショートカット

| Key | Action           |
| --- | ---------------- |
| +   | 拡大               |
| -   | 縮小               |
| 0   | リセット             |
| R   | リロード             |
| S   | Safe Area ON/OFF |
| D   | Debug ON/OFF     |

---

## 推奨倍率

| Zoom |
| ---- |
| 1.00 |
| 0.95 |
| 0.90 |
| 0.85 |
| 0.80 |

---

# Safe Area Overlay

## 必須

調整用Overlayを実装する。

---

## 表示内容

* 四隅マーカー
* 枠線
* センターライン
* グリッド
* テストパターン

---

## 実装

透明Overlay Widgetを最前面に重ねる。

```python
Qt.WA_TransparentForMouseEvents
```

を設定。

描画には：

```python
QPainter
```

を使用。

---

# 自動余白カラー追従

## 目的

余白部分をWebページ背景色へ自動追従させる。

---

## 動作

Webページの：

```javascript
window.getComputedStyle(document.body).backgroundColor
```

を取得。

MainWindow背景色へ反映する。

---

## 対応

以下順で背景色取得：

1. body
2. html
3. ダークモード推定
4. デフォルト黒

---

## SPA対応

React/Vueなどへ対応するため：

* 定期監視
* またはMutationObserver

を使用する。

---

# 設定保存

## 保存内容

* URL
* Zoom
* Margin
* Fullscreen状態
* SafeArea状態
* DisplayScreen
* Background追従設定

---

## 保存形式

JSONを使用。

---

## 例

```json
{
  "url": "https://example.com",
  "zoom": 0.9,
  "margin": 40,
  "fullscreen": true,
  "safe_area": false,
  "screen": "HDMI-1",
  "auto_margin_color": true
}
```

---

# HDMI監視

## 必須

画面追加/削除イベントへ対応。

---

## 対応内容

HDMI切断時：

* DisplayWindowを閉じる
* ControlWindowへ退避

HDMI復帰時：

* 自動でTV側へ再配置

---

# kiosk仕様

## DisplayWindow

* ESC無効
* 右クリック無効
* タイトルバー無し
* Alt+F4抑制可能なら対応

---

# デバッグ表示

## 表示内容

* 現在解像度
* Zoom倍率
* Margin
* FPS
* GPU状態
* URL
* 出力スクリーン

---

# Raspberry Pi対応

## 推奨

* Raspberry Pi 4以上
* GPU有効化
* Openbox kiosk

---

# 推奨ディレクトリ構成

```text
project/
├─ main.py
├─ windows/
│   ├─ control_window.py
│   └─ display_window.py
├─ overlays/
│   ├─ safe_area.py
│   └─ debug_overlay.py
├─ browser/
│   └─ webview.py
├─ settings/
│   ├─ config.json
│   └─ settings_manager.py
├─ home/
│   └─ home_page.html
├─ utils/
└─ assets/
```

---

# 開発優先順位

## Phase 1

* Web表示
* HOME
* Zoom
* Margin
* 設定保存
* セカンドスクリーン自動検出

---

## Phase 2

* Safe Area
* 自動背景色追従
* Debug Overlay
* HDMI監視

---

## Phase 3

* kiosk強化
* Raspberry Pi最適化
* 通信監視
* オフライン画面

---

# 成功条件

以下を満たせば成功：

* 古いテレビでもUIが見切れない
* HDMI接続時に自動でTV表示される
* 1画面環境では通常ブラウザとして安全動作する
* 調整が簡単
* 安定動作する
