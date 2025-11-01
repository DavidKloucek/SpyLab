import os

from PIL import Image


def crop_and_save(image_path: str, x: int, y: int, w: int, h: int, output_path: str, overwrite: bool) -> str:
    if not overwrite and os.path.exists(output_path):
        return output_path

    img = Image.open(image_path)
    cropped_img = img.crop((x, y, x + w, y + h))

    if cropped_img.mode == "RGBA":
        cropped_img = cropped_img.convert("RGB")

    cropped_img.save(output_path)

    return output_path
