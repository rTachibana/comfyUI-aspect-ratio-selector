from .nodes import AspectRatioSelectorExtension


async def comfy_entrypoint() -> AspectRatioSelectorExtension:
    return AspectRatioSelectorExtension()
