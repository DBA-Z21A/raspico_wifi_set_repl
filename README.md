# Pico W WebSerial Toolkit

Raspberry Pi Pico W 用の Web Serial API 通信・WiFi設定・WiFiパスワードの暗号化・HTTPアクセス・REPL制御などを一体化した MicroPython / JavaScript プロジェクトです。
PCとUSBケーブルがあれば、専門知識のない利用者でもWiFi接続情報を設定できるようになります。
また、Raspberry Pi Pico Wとの通信機能はHTML＋JavaScriptのみで実装していますので、サーバサイドで独自に利用者ごとの認証情報を生成・追加しRaspberry Pi Pico W側に保存させる事も可能です。

## 機能一覧

- Web Serial API によるブラウザからの直接通信（USB経由）
- 暗号化された WiFi 設定ファイルの保存と復号
- BOOTSEL ボタンを用いた安全な再設定モード
- ソフトウェアによる REPL リセット（Ctrl+C / Ctrl+D / Ctrl+B 相当）
- HTTPアクセスとNTPによる時刻同期
- MicroPython（Raspberry Pi Pico W）向けに最適化された軽量設計

## 対象環境

- Raspberry Pi Pico W
- MicroPython（v1.20 以降を推奨）
- Web Serial API 対応ブラウザ（例：Google Chrome、Microsoft Edge）

## 使用方法

1. 開発者は `wifisetting.py` を Raspberry Pi Pico W に書き込み、利用者に提供
2. 利用者は Pico W を PC と USB で接続し、起動
3. 利用者は HTTPS サーバに設置された `pico_repl3.html` にアクセス
4. ブラウザ上の Web Serial API を通じて WiFi 情報を Pico W に送信
5. `mail.py` 等のアプリケーションコードを実行  
   （サンプルとして BOOTSEL ボタンで設定ファイルを初期化可能な `mail.py` を同梱）

## 補足資料（開発メモ・参考資料）

以下のファイルは開発経緯の記録や、Blog執筆用の試作コードなどを目的に残しています。
本プロジェクトの実行には不要ですが、技術的背景に関心のある方はご参照ください。

- `pico/firmware/`
  - test0.py
  - test1.py
  - test2.py
- `web/frontend/`
  - pico_repl.html
  - pico_repl2.html
  - pico_repl2_5.html
  - pico_repl2.js
  - web_serial_test.html

## ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。

修正・派生を行った場合は、可能な限りフィードバックをお寄せください。
詳しくは下記「貢献」セクションもご覧ください。

## 貢献

バグ報告、機能提案、プルリクエストなど大歓迎です！

特に MicroPython に関する本格的な開発は今回が初めての取り組みですので、
改善点やアドバイスをいただけると非常に助かります。

## 作者

- GitHub: [hironori maruyama](https://github.com/DBA-Z21A)
