# ComfyUI Aspect Ratio Selector

指定したアスペクト比に合わせて、選択したモデルの基準解像度（ピクセル総数）に最も近い最適な空の潜在空間 (Empty Latent) を生成する ComfyUI カスタムノードです。

[English README](./README.md)

## 特徴

- **動的な解像度計算**: SD 1.5, SDXL, FLUX などのモデルの基準となるピクセル面積を維持したまま、指定したアスペクト比の解像度を自動で計算します。
- **モデル固有の制約への準拠**: 各モデルで要求されるピクセル数の倍数制約（例: SDXLなら64の倍数、FLUXなら16の倍数）に自動で丸められます。
- **カスタマイズ可能なモデル設定**: 同梱の `config.json` を編集することで、新しいモデルや任意のベース解像度を簡単に追加・変更できます。

## ノード詳細
### Aspect Ratio Selector
入力:
- `model`: 対象のモデル名（SD 1.5, SDXL, FLUX.1 など）を選択します。ここで基準解像度やチャネル数が決まります。
- `aspect_ratio`: 用意されたアスペクト比（1:1, 3:4, 2:3, 5:8, 9:16, 9:21）から選択します。
- `orientation`: Portrait (縦長) または Landscape (横長) を指定します。
- `batch_size`: 生成するバッチのサイズです。

出力:
- `width`: 計算された幅 (ピクセル単位)。
- `height`: 計算された高さ (ピクセル単位)。
- `latent`: 生成された空の潜在空間。

## インストール方法

ComfyUI の `custom_nodes` ディレクトリにこのリポジトリをクローンしてください。

```bash
cd ComfyUI/custom_nodes
git clone <リポジトリのURL> comfyui-aspect-ratio-selector
```

その後、ComfyUI を再起動してください。

## 設定

ノードのディレクトリ内にある `config.json` を編集することで、モデルの設定をカスタマイズできます。ベース幅、ベース高さ、丸めの基準(multiple_of)、および潜在空間のチャネル数を設定できます。

`config.json` の設定例:
```json
{
  "name": "SDXL",
  "base_width": 1024,
  "base_height": 1024,
  "multiple_of": 64,
  "latent_channels": 4
}
```
※ `config.json` の編集後は、変更を反映させるために ComfyUI の再起動が必要です。
