"""
ComfyUI V3 node: Aspect Ratio Selector

モデルの基準解像度を元にアスペクト比を維持した空の潜在空間を生成します。
解像度は「基準ピクセル数を一定に保ちながら指定アスペクト比に最も近い値」
として計算し、モデルごとの multiple_of に丸めます。

例 (SDXL, 基準 1024×1024, multiple_of=64):
  1:1  Portrait  → 1024×1024
  3:4  Portrait  →  896×1152
  9:16 Portrait  →  768×1344
  9:21 Portrait  →  640×1536
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any
from typing_extensions import override

import torch
from comfy_api.latest import ComfyExtension, io

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config.json"

# ---------------------------------------------------------------------------
# アスペクト比定義  (短辺比 : 長辺比)
# ---------------------------------------------------------------------------

_ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "1:1":  (1,  1),
    "3:4":  (3,  4),
    "2:3":  (2,  3),
    "5:8":  (5,  8),
    "9:16": (9,  16),
    "9:21": (9,  21),
}

_ORIENTATIONS = ["Portrait", "Landscape"]

# ---------------------------------------------------------------------------
# デフォルト設定（config.json が読めない場合のフォールバック）
# ---------------------------------------------------------------------------

_DEFAULT_MODELS: list[dict[str, Any]] = [
    {"name": "SD 1.5",  "base_width": 512,  "base_height": 512,  "multiple_of": 8,  "latent_channels": 4},
    {"name": "SDXL",    "base_width": 1024, "base_height": 1024, "multiple_of": 64, "latent_channels": 4},
    {"name": "FLUX.1",  "base_width": 1024, "base_height": 1024, "multiple_of": 16, "latent_channels": 16},
    {"name": "FLUX.2",  "base_width": 1024, "base_height": 1024, "multiple_of": 16, "latent_channels": 16},
]

# ---------------------------------------------------------------------------
# 設定の読み込み（モジュールロード時に一度だけ実行）
# ---------------------------------------------------------------------------

def _load_models() -> list[dict[str, Any]]:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        models = cfg.get("models")
        if not isinstance(models, list) or not models:
            raise ValueError("'models' が空またはリストではありません")
        # 必須フィールドの検証
        required = {"name", "base_width", "base_height", "multiple_of", "latent_channels"}
        for m in models:
            missing = required - m.keys()
            if missing:
                raise ValueError(f"モデル {m.get('name', '?')} にフィールドが不足: {missing}")
        return models
    except Exception as e:
        log.warning(f"[AspectRatioSelector] config.json の読み込みに失敗しました: {e} — デフォルト設定を使用します")
        return _DEFAULT_MODELS


_MODELS: list[dict[str, Any]] = _load_models()
_MODEL_NAMES: list[str] = [m["name"] for m in _MODELS]
_MODEL_MAP: dict[str, dict[str, Any]] = {m["name"]: m for m in _MODELS}


# ---------------------------------------------------------------------------
# 解像度計算
# ---------------------------------------------------------------------------

def compute_resolution(
    base_w: int,
    base_h: int,
    ar_short: int,
    ar_long: int,
    multiple_of: int,
) -> tuple[int, int]:
    """
    基準ピクセル数 (base_w × base_h) を保ちながら、
    アスペクト比 ar_short:ar_long に最も近い解像度を計算します。

    Returns
    -------
    (long_px, short_px)
        長辺・短辺のピクセル数（どちらも multiple_of の倍数）。
    """
    pixel_budget = base_w * base_h
    long_px  = math.sqrt(pixel_budget * ar_long  / ar_short)
    short_px = math.sqrt(pixel_budget * ar_short / ar_long)
    long_px  = max(multiple_of, round(long_px  / multiple_of) * multiple_of)
    short_px = max(multiple_of, round(short_px / multiple_of) * multiple_of)
    return int(long_px), int(short_px)


# ---------------------------------------------------------------------------
# ノード定義
# ---------------------------------------------------------------------------

class AspectRatioSelectorNode(io.ComfyNode):
    """
    モデルとアスペクト比を選んで、適切なサイズの空の潜在空間を生成します。

    解像度はモデルの基準解像度（ピクセル総数）を維持したまま
    指定アスペクト比に合わせて計算されます。
    カスタムモデルを追加するには config.json を編集して ComfyUI を再起動してください。
    """

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AspectRatioSelector",
            display_name="Aspect Ratio Selector",
            category="latent",
            description=(
                "モデルとアスペクト比から最適な解像度の空の潜在空間を生成します。\n"
                "解像度はモデルの基準ピクセル数を維持しながら計算されます。\n"
                "カスタムモデルは config.json を編集して追加できます。"
            ),
            search_aliases=["resolution", "aspect ratio", "empty latent", "latent size", "canvas size"],
            inputs=[
                io.Combo.Input(
                    "model",
                    options=_MODEL_NAMES,
                    default=_MODEL_NAMES[0] if _MODEL_NAMES else None,
                    tooltip="モデルを選択します。基準解像度とチャネル数が決まります。",
                ),
                io.Combo.Input(
                    "aspect_ratio",
                    options=list(_ASPECT_RATIOS.keys()),
                    default="1:1",
                    tooltip=(
                        "アスペクト比（短辺:長辺）\n"
                        "  1:1  正方形\n"
                        "  3:4  一般的な縦長\n"
                        "  2:3  写真縦長\n"
                        "  9:16 スマートフォン縦\n"
                        "  9:21 シネマスコープ縦"
                    ),
                ),
                io.Combo.Input(
                    "orientation",
                    options=_ORIENTATIONS,
                    default="Portrait",
                    tooltip=(
                        "Portrait  : 縦長（height > width）\n"
                        "Landscape : 横長（width > height）\n"
                        "（1:1 の場合は無効）"
                    ),
                ),
                io.Int.Input(
                    "batch_size",
                    default=1,
                    min=1,
                    max=64,
                    tooltip="バッチ数（一度に生成する画像の枚数）。",
                ),
            ],
            outputs=[
                io.Int.Output("width",  display_name="Width"),
                io.Int.Output("height", display_name="Height"),
                io.Latent.Output("latent", display_name="Latent"),
            ],
        )

    @classmethod
    @override
    def execute(
        cls,
        model: str,
        aspect_ratio: str,
        orientation: str,
        batch_size: int,
    ) -> io.NodeOutput:
        cfg = _MODEL_MAP.get(model, _MODELS[0])
        base_w: int         = cfg["base_width"]
        base_h: int         = cfg["base_height"]
        multiple_of: int    = cfg["multiple_of"]
        latent_ch: int      = cfg["latent_channels"]

        ar_short, ar_long = _ASPECT_RATIOS.get(aspect_ratio, (1, 1))

        long_px, short_px = compute_resolution(base_w, base_h, ar_short, ar_long, multiple_of)

        if orientation == "Landscape":
            width, height = long_px, short_px
        else:  # Portrait
            width, height = short_px, long_px

        samples = torch.zeros([batch_size, latent_ch, height // 8, width // 8])
        latent = {"samples": samples}

        return io.NodeOutput(width, height, latent)


# ---------------------------------------------------------------------------
# 拡張登録
# ---------------------------------------------------------------------------

class AspectRatioSelectorExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [AspectRatioSelectorNode]
