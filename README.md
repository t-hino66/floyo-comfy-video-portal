# Floyo & ComfyUI Video Workflows Portal

Floyo UI および ComfyUI での動画制作ワークフロー、最新オープンソース動画モデル情報、Redditコミュニティのリアルタイムノウハウを集約・可視化する GitHub Pages 対応のポータルWebサイトです。

## 🌟 主な特徴

- **無料・オープンソースモデル基準 (Free & Open-Source First)**
  - **LTX 2.3** (Floyoで標準利用可能な軽量・高画質I2V/T2Vモデル)
  - **Wan 2.1 / Wan 2.2** (最新の強力なオープンソース動画生成モデル)
  - **AnimateDiff** (アニメ風動画制作の定番)
  - **HunyuanVideo** (T2Vオープンソースモデル)
- **Partner Node / 有料クレジット注意喚起**
  - Kling, Seedance, Moonvalley, Pixverse 等の Floyo API ウォレット消費モデルを `Paid / Partner Risk` として明確にタグ付け分類。
- **Reddit リアルタイム巡回**
  - `r/comfyui`, `r/Floyo`, `r/StableDiffusion` 等の動画関連スレッドを自動集約。
- **GitHub Actions による完全自動デプロイ**
  - 毎日自動でRSS情報を巡回し、GitHub Pages に最新サイトをパブリッシュ。

## 🚀 ディレクトリ構成

- `extract_floyo_comfy_knowhow.py`: Reddit RSS巡回および動画ワークフローデータ集約スクリプト
- `build_floyo_site.py`: `floyo_comfy_database.json` からシングルファイル `index.html` を動的生成するビルドスクリプト
- `index.html`: モダンなグラスモフィズムデザインで構築されたポータルWebサイト
- `.github/workflows/deploy.yml`: GitHub Actions 自動更新・Pages デプロイ設定

## 💻 ローカルでの実行・動作確認

1. **最新データの取得とデータベース作成**
   ```bash
   python3 extract_floyo_comfy_knowhow.py
   ```
2. **Webサイトのビルド**
   ```bash
   python3 build_floyo_site.py
   ```
3. **ローカルプレビュー**
   ```bash
   python3 -m http.server 8000
   ```
   ブラウザで `http://localhost:8000` を開くことで動作を確認できます。

## 🌐 GitHub Pages 公開手順

1. 本リポジトリを GitHub にプッシュします。
2. リポジトリの **Settings > Pages** を開きます。
3. **Source** を `GitHub Actions` に設定します。
4. 毎日自動更新およびPagesへの自動反映が実行されます。
