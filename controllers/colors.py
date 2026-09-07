import json
from enum import Enum
from typing import List, Tuple

import numpy as np
from PIL import Image


class Color(Enum):
    TRANSPARENT     = (0, 0, 0, 0, True)
    BLACK           = (0, 0, 0, 255, True)
    DARK_GRAY       = (60, 60, 60, 255, True)
    GRAY            = (120, 120, 120, 255, True)
    LIGHT_GRAY      = (210, 210, 210, 255, True)
    WHITE           = (255, 255, 255, 255, True)
    DEEP_RED        = (96, 0, 24, 255, True)
    RED             = (237, 28, 36, 255, True)
    ORANGE          = (255, 127, 39, 255, True)
    GOLD            = (246, 170, 9, 255, True)
    YELLOW          = (249, 221, 59, 255, True)
    LIGHT_YELLOW    = (255, 250, 188, 255, True)
    DARK_GREEN      = (14, 185, 104, 255, True)
    GREEN           = (19, 230, 123, 255, True)
    LIGHT_GREEN     = (135, 255, 94, 255, True)
    DARK_TEAL       = (12, 129, 110, 255, True)
    TEAL            = (16, 174, 166, 255, True)
    LIGHT_TEAL      = (19, 225, 190, 255, True)
    DARK_BLUE       = (40, 80, 158, 255, True)
    BLUE            = (64, 147, 228, 255, True)
    CYAN            = (96, 247, 242, 255, True)
    INDIGO          = (107, 80, 246, 255, True)
    LIGHT_INDIGO    = (153, 177, 251, 255, True)
    DARK_PURPLE     = (120, 12, 153, 255, True)
    PURPLE          = (170, 56, 185, 255, True)
    LIGHT_PURPLE    = (224, 159, 249, 255, True)
    DARK_PINK       = (203, 0, 122, 255, True)
    PINK            = (236, 31, 128, 255, True)
    LIGHT_PINK      = (243, 141, 169, 255, True)
    DARK_BROWN      = (104, 70, 52, 255, True)
    BROWN           = (149, 104, 42, 255, True)
    BEIGE           = (248, 178, 119, 255, True)
    MEDIUM_GRAY     = (170, 170, 170, 255, False)
    DARK_RED        = (165, 14, 30, 255, False)
    LIGHT_RED       = (250, 128, 114, 255, False)
    DARK_ORANGE     = (228, 92, 26, 255, False)
    LIGHT_TAN       = (214, 181, 148, 255, False)
    DARK_GOLDENROD  = (156, 132, 49, 255, False)
    GOLDENROD       = (197, 173, 49, 255, False)
    LIGHT_GOLDENROD = (232, 212, 95, 255, False)
    DARK_OLIVE      = (74, 107, 58, 255, False)
    OLIVE           = (90, 148, 74, 255, False)
    LIGHT_OLIVE     = (132, 197, 115, 255, False)
    DARK_CYAN       = (15, 121, 159, 255, False)
    LIGHT_CYAN      = (187, 250, 242, 255, False)
    LIGHT_BLUE      = (125, 199, 255, 255, False)
    DARK_INDIGO     = (77, 49, 184, 255, False)
    DARK_SLATE_BLUE = (74, 66, 132, 255, False)
    SLATE_BLUE      = (122, 113, 196, 255, False)
    LIGHT_SLATE_BLUE= (181, 174, 241, 255, False)
    LIGHT_BROWN     = (219, 164, 99, 255, False)
    DARK_BEIGE      = (209, 128, 81, 255, False)
    LIGHT_BEIGE     = (255, 197, 165, 255, False)
    DARK_PEACH      = (155, 82, 73, 255, False)
    PEACH           = (209, 128, 120, 255, False)
    LIGHT_PEACH     = (250, 182, 164, 255, False)
    DARK_TAN        = (123, 99, 82, 255, False)
    TAN             = (156, 132, 107, 255, False)
    DARK_SLATE      = (51, 57, 65, 255, False)
    SLATE           = (109, 117, 141, 255, False)
    LIGHT_SLATE     = (179, 185, 209, 255, False)
    DARK_STONE      = (109, 100, 63, 255, False)
    STONE           = (148, 140, 107, 255, False)
    LIGHT_STONE     = (205, 197, 158, 255, False)


class ColorConfig:
    def __init__(self, config_file='data/color_config.json'):
        self.config_file = config_file
        self._overrides = {}
        self.load_config()

    def load_config(self):
        """Loads configuration from a JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                self._overrides = json.load(f)
        except FileNotFoundError:
            self._overrides = {}
    
    def save_config(self):
        """Saves the current configuration to a JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self._overrides, f, indent=2)
    
    def get_bool(self, color_name):
        """Gets the bool of a color, using override if it exists"""
        if color_name in self._overrides:
            return self._overrides[color_name]
        return Color[color_name].value[4]
    
    def get_rgb(self, color_name):
        """Gets the RGB of a color"""
        return Color[color_name].value[:3]
    
    def set_bool(self, color_name, value):
        """Sets the bool of a color"""
        self._overrides[color_name] = value
    
    def reset(self, color_name=None):
        """Resets to default values"""
        if color_name:
            self._overrides.pop(color_name, None)
        else:
            self._overrides = {}


# Instance a global configuration instance
color_config = ColorConfig()


# List in exact order
def get_color_id(rgb):
    rgb_tuple = tuple(rgb)
    for idx, color in enumerate(list(Color)):
        if color.value[:4] == rgb_tuple:
            return color.name, idx, color_config.get_bool(color.name)
    return None, None, None


def get_palette(only_owned: bool = False) -> Tuple[List[str], List[int], np.ndarray]:
    """
    Build the list of opaque palette colors, optionally limited to owned ones.

    Args:
        only_owned: If True, skip the colors not currently owned

    Returns:
        Tuple with the color names, their ids and their RGB values as an array
    """
    names, ids, rgbs = [], [], []
    for idx, color in enumerate(list(Color)):
        # Transparency is handled by the alpha channel, not by distance
        if color.value[3] == 0:
            continue
        if only_owned and not color_config.get_bool(color.name):
            continue
        names.append(color.name)
        ids.append(idx)
        rgbs.append(color.value[:3])
    return names, ids, np.array(rgbs, dtype=np.float32)


def _nearest_palette_indices(rgbs: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    Find the closest palette entry for every given RGB value.

    Uses the "redmean" weighted distance, which matches human perception much
    better than a plain euclidean distance while staying cheap to compute.

    Args:
        rgbs: Array of shape (N, 3) with the colors to match
        palette: Array of shape (P, 3) with the available colors

    Returns:
        Array of shape (N,) with the index of the closest palette entry
    """
    rmean = (rgbs[:, None, 0] + palette[None, :, 0]) / 2
    delta = rgbs[:, None, :] - palette[None, :, :]
    dr, dg, db = delta[..., 0], delta[..., 1], delta[..., 2]
    distance = (2 + rmean / 256) * dr ** 2 + 4 * dg ** 2 + (2 + (255 - rmean) / 256) * db ** 2
    return np.argmin(distance, axis=1)


def get_nearest_color(rgba, only_owned: bool = False):
    """
    Get the palette color closest to an arbitrary RGBA value.

    Args:
        rgba: The (r, g, b, a) color to approximate
        only_owned: If True, only consider the colors currently owned

    Returns:
        Tuple with the color name, its id and whether it is owned
    """
    if len(rgba) > 3 and rgba[3] == 0:
        return Color.TRANSPARENT.name, 0, color_config.get_bool(Color.TRANSPARENT.name)

    names, ids, palette = get_palette(only_owned)
    if not names:
        return None, None, None

    rgbs = np.array([rgba[:3]], dtype=np.float32)
    match = int(_nearest_palette_indices(rgbs, palette)[0])
    return names[match], ids[match], color_config.get_bool(names[match])


def quantize_image(image_path: str, only_owned: bool = False, alpha_threshold: int = 128) -> int:
    """
    Snap every pixel of an image to the closest wplace palette color.

    Images edited outside of wplace (resized, antialiased, JPEG compressed...)
    contain colors that do not exist in the canvas, so they can never be
    matched or repainted. Rewriting them in place keeps the comparison and the
    fix commands consistent.

    Args:
        image_path: Path to the image to quantize (overwritten in place)
        only_owned: If True, only snap to the colors currently owned
        alpha_threshold: Pixels below this alpha become fully transparent

    Returns:
        Number of pixels that were changed
    """
    image = Image.open(image_path).convert("RGBA")
    pixels = np.array(image)
    original = pixels.copy()

    alpha = pixels[..., 3]
    transparent = alpha < alpha_threshold
    pixels[transparent] = (0, 0, 0, 0)
    pixels[~transparent, 3] = 255

    opaque = pixels[~transparent][:, :3]
    if opaque.size:
        # Match unique colors only, an image has far more pixels than colors
        unique, inverse = np.unique(opaque, axis=0, return_inverse=True)
        inverse = inverse.reshape(-1)
        _, _, palette = get_palette(only_owned)
        match = _nearest_palette_indices(unique.astype(np.float32), palette)
        pixels[~transparent, :3] = palette[match[inverse]].astype(np.uint8)

    # Pixels that were already invisible do not count, only their hidden RGB
    # noise was normalized, which changes nothing on the canvas
    visible = np.any(pixels != original, axis=2) & (original[..., 3] != 0)
    if np.any(pixels != original):
        Image.fromarray(pixels, mode="RGBA").save(image_path)
    return int(np.count_nonzero(visible))


# if __name__ == "__main__":
#     # See original values
#     name, id_, enabled = get_color_id([237, 28, 36, 255])
#     print(f"{name} {id_} enabled={enabled}")  # RED 7 enabled=True
    
#     # Change config
#     color_config.set_bool('RED', False)
#     color_config.save_config()
    
#     # See modified value
#     name, id_, enabled = get_color_id([237, 28, 36, 255])
#     print(f"{name} {id_} enabled={enabled}")  # RED 7 enabled=False
    
#     # Reset
#     color_config.reset('RED')
#     color_config.save_config()