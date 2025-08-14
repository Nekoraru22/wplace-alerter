import cv2
import json
import os
import time
import requests
import datetime
import numpy as np

from PIL import Image
from enum import Enum
from selenium import webdriver
from typing import List, Dict, Tuple

from colorama import Fore, init
from selenium.webdriver.chrome.options import Options

from data.colors import Color, get_color_id

init(autoreset=True)

# Van en orden literalmente xD
class ColorType(Enum):
    BLACK = 1
    GRAY = 4
    PINK = 28

Color = ColorType               # RGB color
Position = Dict[str, int]       # {'x': int, 'y': int}
Pixel = Dict[Color, Position]


class WPlace:

    def __init__(self):
        self.headers = {
            'Host': 'backend.wplace.live',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'image/webp,*/*',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://wplace.live/',
            'Origin': 'https://wplace.live',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
            'TE': 'trailers'
        }

        # Load image with Selenium
        options = Options()
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.driver = webdriver.Chrome(options=options)

    def __del__(self):
        self.driver.quit()

    def convert_to_api(self, pixels: List[Pixel]) -> Tuple[List[int], List[int]]:
        """
        Convert pixel data to API format.

        Args:
            pixels: List of pixels to convert

        Returns:
            Tuple of (colors, coords) where colors is a list of color IDs and coords is a list of coordinates
        """
        colors = []
        coords = []
        for pixel in pixels:
            for color, position in pixel.items():
                colors.append(color.value)
                coords.append(position['x'])
                coords.append(position['y'])
        return colors, coords

    def generate_command(self, pixels) -> str:
        """
        Generate a js command to fix the pixels

        Args:
            pixels: List of pixels to fix

        Returns:
            str: The generated js command
        """
        pixel_objects = []
        for pixel in pixels:
            pixel_objects.append({
                "color": pixel['color'],
                "x": pixel['x'],
                "y": pixel['y']
            })

        colors, coords = self.convert_to_api(pixel_objects)
        command = f"```js\nfixPixels({json.dumps(colors)}, {json.dumps(coords)})\n```"
        return command

    def paint(self, url: str, pixels: List[Pixel]) -> None:
        """
        NOT WORKING -> Cloudflare protection
        Function that paints a pixel by API

        Args:
            pixels: List of pixels to paint
        """
        colors, coords = self.convert_to_api(pixels)
        data = {"colors": colors, "coords": coords}
        response = requests.post(url, headers=self.headers, json=data)
        print(response.json())

    def check_pixel(self, url: str, position: Position) -> None:
        """
        NOT WORKING -> Cloudflare protection
        Gets info about a pixel.

        Args:
            position: The position of the pixel to check.
        """
        url = f'{url}?x={position["x"]}&y={position["y"]}'
        response = requests.get(url, headers=self.headers)
        print(response.json())

    def crop_image(self, image_path: str, crop_box: Tuple[int, int, int, int]) -> None:
        """
        Crop an image and save the result.
        
        Args:
            image_path: Path to the input image
            crop_box: (left, top, right, bottom) coordinates for cropping
        """
        # Open the image
        image = Image.open(image_path)

        # Crop the image using the specified box
        cropped_image = image.crop(crop_box)

        # Save the cropped image
        cropped_image.save(image_path)

    def compare_image(self, good: str, new: str, threshold: float = 0.0) -> bool:
        """
        Compares two images and returns True if they are similar within a certain threshold.

        Args:
            good: Path to the "good" image
            new: Path to the "new" image
            threshold: Similarity threshold (lower is more strict)

        Returns:
            bool: True if images are similar, False otherwise
        """
        # Load images with alpha channel to consider transparency differences
        image1 = cv2.imread(good, cv2.IMREAD_UNCHANGED)
        image2 = cv2.imread(new, cv2.IMREAD_UNCHANGED)

        # Check if images are loaded successfully
        if image1 is None or image2 is None:
            print(Fore.LIGHTRED_EX + "Error: Could not read one or both image files.")
            return False

        # Ensure images have the same dimensions
        if image1.shape != image2.shape:
            print(Fore.LIGHTRED_EX + f"Error: Image dimensions do not match. Image1: {image1.shape}, Image2: {image2.shape}")
            return False # Cannot compare pixel by pixel if dimensions differ

        # Calculate the Mean Squared Error (MSE) across all channels
        diff = image1.astype("float") - image2.astype("float")
        err = np.mean(diff ** 2)
        return bool(err <= threshold)

    def get_changed_pixels(self, good: str, new: str) -> List[Dict[str, Dict[str, int]]]:
        """
        Locate pixels that differ between two images.

        Args:
            good: Path to the reference image.
            new: Path to the new image to compare.

        Returns:
            List of dictionaries with the x, y coordinates and RGBA color of the
            changed pixels in the new image.
        """
        image1 = cv2.imread(good, cv2.IMREAD_UNCHANGED)
        image2 = cv2.imread(new, cv2.IMREAD_UNCHANGED)

        if image1 is None or image2 is None:
            return []

        if image1.shape != image2.shape:
            return []

        diff = cv2.absdiff(image1, image2)
        ys, xs = np.where(np.any(diff != 0, axis=2))

        changed = []
        for x, y in zip(xs, ys):
            pixel = image2[y, x]
            b, g, r, a = pixel
            color = (int(r), int(g), int(b), int(a))
            changed.append({
                "x": int(x),
                "y": int(y),
                "color": color
            })
        return changed

    def check_change(self, api_image: str, coords: Tuple[int, int, int, int], good_image_path: str, new_image_path: str) -> None:
        """
        Downloads the new image and checks for changes against the last image.

        Args:
            api_image: URL of the API image
            coords: Coordinates for cropping the image
            good_image_path: Path to the "good" image
            new_image_path: Path to the "new" image
        """
        self.driver.get(api_image)

        # Get network logs and download the image
        logs = self.driver.get_log("performance")
        for log in logs:
            message = json.loads(log["message"])
            if message["message"]["method"] == "Network.responseReceived":
                response = message["message"]["params"]["response"]
                if response["url"].endswith(".png"):
                    # Get response body
                    response_body = self.driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {"requestId": message["message"]["params"]["requestId"]}
                    )
                    
                    # Decode and save
                    import base64
                    image_data = base64.b64decode(response_body["body"])
                    with open(new_image_path, 'wb') as file:
                        file.write(image_data)
                    break

        # Crop the image
        self.crop_image(new_image_path, coords)

        # Check if good image exists
        if not os.path.exists(good_image_path):
            print(Fore.LIGHTYELLOW_EX + "No se encontró la imagen buena, guardando la nueva imagen como buena.")
            with open(good_image_path, 'wb') as f:
                f.write(open(new_image_path, 'rb').read())
            return

        # Check for changes
        if not self.compare_image(good_image_path, new_image_path):
            changed = self.get_changed_pixels(good_image_path, new_image_path)
            print(Fore.LIGHTRED_EX + "¡ALERTA! Algún pixel ha cambiado!!! :<")
            for pixel in changed:
                name, id_ = get_color_id(pixel['color'])
                print(Fore.LIGHTRED_EX + f"    Pixel cambiado en X={coords[0] + int(str(pixel['x']))}, Y={coords[1] + int(str(pixel['y']))} con color {name}(id: {id_})")
            self.send_alert(
                "# ¡ALERTA! Algún pixel ha cambiado!!! :< (Antes, después)\n\n## Comando para arreglar los píxeles:\n" +
                self.generate_command(changed),
                good_image_path,
                new_image_path
            )
            # Replace the new image with the good image
            with open(good_image_path, 'wb') as f:
                f.write(open(new_image_path, 'rb').read())
        else:
            print(Fore.LIGHTGREEN_EX + "No se detectaron cambios en los píxeles.")

    def send_alert(self, message: str, image_path1: str, image_path2: str) -> None:
        """
        Sends an alert message with attached images to a Discord webhook.

        Args:
            message: The alert message to send.
            image_path1: Path to the first image to attach.
            image_path2: Path to the second image to attach.
        """
        discord_webhook_url = arts_data["discord_webhook_url"]
        files = {}
        payload = {"content": message}

        if image_path1 and os.path.exists(image_path1):
            try:
                files["file1"] = (os.path.basename(image_path1), open(image_path1, "rb"))
            except IOError:
                print(Fore.LIGHTRED_EX + f"Error: No se pudo abrir la imagen 1 en {image_path1}")

        if image_path2 and os.path.exists(image_path2):
            try:
                files["file2"] = (os.path.basename(image_path2), open(image_path2, "rb"))
            except IOError:
                print(Fore.LIGHTRED_EX + f"Error: No se pudo abrir la imagen 2 en {image_path2}")

        try:
            response = requests.post(discord_webhook_url, data=payload, files=files)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print(Fore.LIGHTRED_EX + f"Error HTTP: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(Fore.LIGHTRED_EX + f"Error de conexión: {errc}")
        except requests.exceptions.Timeout as errt:
            print(Fore.LIGHTRED_EX + f"Tiempo de espera agotado: {errt}")
        except requests.exceptions.RequestException as err:
            print(Fore.LIGHTRED_EX + f"Error inesperado: {err}")
        finally:
            # Ensure files are closed after sending
            for f in files.values():
                f[1].close()


def main(arts_data: dict):
    wplace = WPlace()
    while True:
        time_info = datetime.datetime.now().isoformat()
        print(f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ {time_info} ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
        try:
            for name in arts_data["arts"]:
                if not arts_data["arts"][name]["track"]: continue
                print(Fore.LIGHTYELLOW_EX + f"Checking art: {Fore.RESET}{name}", end=' -> ')

                # Get art details
                art = arts_data["arts"][name]
                api_image = art["api_image"]
                coords = (
                    art["start_coords"]["x"], art["start_coords"]["y"], 
                    art["end_coords"]["x"], art["end_coords"]["y"]
                )
                path = f"data/{name}/"

                # Create folder if it doesn't exist
                os.makedirs(path, exist_ok=True)

                # Check for changes
                wplace.check_change(api_image, coords, f'{path}good.png', f'{path}new.png')
                time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(arts_data["cooldown"])
        print()
    
    # Proves
    # pixels: List[Pixel] = [
    #     {
    #         Color(ColorType.PINK): {'x': 40, 'y': 162},
    #     }
    # ]
    # wplace.check_pixel(api_image.replace(".png", ""), pixels[0])
    # wplace.paint(api_image.replace(".png", ""), pixels)


if __name__ == "__main__":
    # Read data
    with open('data/arts.json') as f:
        arts_data = json.load(f)
    main(arts_data)
