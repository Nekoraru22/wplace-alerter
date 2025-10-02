import json
from enum import Enum
from traceback import print_tb
from turtle import color


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