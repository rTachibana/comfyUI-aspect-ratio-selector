# ComfyUI Aspect Ratio Selector

A custom node for ComfyUI that generates an empty latent image with the optimal resolution for a given aspect ratio, while preserving the foundational pixel budget (base resolution) of the selected model.

[日本語のREADMEはこちら](./README_jp.md)

## Features

- **Dynamic Resolution Calculation**: Maintains the total pixel count appropriate for models like SD 1.5, SDXL, and FLUX, adjusting the width and height to match your desired aspect ratio.
- **Model-Specific Alignment**: Automatically rounds dimensions to the nearest appropriate multiple for the selected model architecture (e.g., multiple of 64 for SDXL, 16 for FLUX).
- **Customizable Models**: Easily add or modify supported models and their base resolutions by editing the included `config.json`.

## Included Node
### Aspect Ratio Selector
Inputs:
- `model`: Choose the target model architecture (SD 1.5, SDXL, FLUX.1, etc.).
- `aspect_ratio`: Choose from standard aspect ratios (1:1, 3:4, 2:3, 5:8, 9:16, 9:21).
- `orientation`: Portrait (vertical) or Landscape (horizontal).
- `batch_size`: Number of latent samples to generate.

Outputs:
- `width`: The calculated width in pixels.
- `height`: The calculated height in pixels.
- `latent`: The generated empty latent space.

## Installation

Clone this repository into your ComfyUI `custom_nodes` directory:

```bash
cd ComfyUI/custom_nodes
git clone <repository_url> comfyui-aspect-ratio-selector
```

Restart ComfyUI.

## Configuration

You can customize the base models, their target resolutions, multiple alignment constraints, and latent channel counts by modifying the `config.json` file located in the node directory.

Example `config.json` entry:
```json
{
  "name": "SDXL",
  "base_width": 1024,
  "base_height": 1024,
  "multiple_of": 64,
  "latent_channels": 4
}
```
*Note: A restart of ComfyUI is required after editing `config.json`.*
