import re
import cv2
import json
import os
import time
import requests
import datetime
import numpy as np

from PIL import Image
from selenium import webdriver
from typing import List, Dict, Tuple

from colorama import Fore, init
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from data.colors import Color, get_color_id

init(autoreset=True)

Position = Dict[str, int]
Pixel = Dict[Color, Position]


class WPlace:

    def __init__(self):
        options = Options()
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.driver = webdriver.Chrome(options=options)

        # Config
        self.driver.set_page_load_timeout(time_to_wait=20) # TimeoutException if page takes too long to load

    def __del__(self):
        self.driver.quit()

    def convert_to_api(self, pixels: List[Pixel]) -> Tuple[List[int], List[int]]:
        """
        DEPRECATED

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
                colors.append(color)
                coords.append(position['x'])
                coords.append(position['y'])
        return colors, coords

    def get_tiles_from_api_url(self, api_image: str) -> Tuple[int, int]:
        """
        Get tile information from the API url.

        Args:
            api_image: The API image URL

        Returns:
            List of tile information
        """
        match = re.search(r'https://backend\.wplace\.live/files/s0/tiles/(\d+)/(\d+)\.png', api_image)
        if match:
            tile_x = int(match.group(1))
            tile_y = int(match.group(2))
            return (tile_x, tile_y)
        return (0, 0)

    # TODO: Move to JS and generate the minimum size command that it builds itself
    def generate_command(self, pixels: list, coords: Tuple[int, int, int, int], api_image: str) -> str:
        """
        Generate a js command to fix the pixels

        Args:
            pixels: List of pixels to fix

        Returns:
            str: The generated js command
        """
        api_tiles = self.get_tiles_from_api_url(api_image)
        commands = []

        counter = 1
        for pixel in pixels:
            # Posición absoluta del píxel
            abs_x = coords[0] + pixel['x']
            abs_y = coords[1] + pixel['y']

            # Color
            r, g, b, a, owned = pixel["old_color"]
            _, color_idx = get_color_id(pixel["old_color"])

            # Avoid paid color pixels
            if color_idx == None:
                if pixel["old_color"][3] != 0:
                    print(Fore.LIGHTRED_EX + f"Skipping pixel {counter}/{len(pixels)}: {pixel} for being an unknown color")
                continue
            elif not owned:
                print(Fore.LIGHTYELLOW_EX + f"Skipping pixel {counter}/{len(pixels)}: {pixel} for being a paid color ({color_idx})")
                continue

            cmd = (
                f'// {counter}/{len(pixels)}\n'
                f'o.set("t=({api_tiles[0]},{api_tiles[1]});p=({abs_x},{abs_y});s=0", {{\n'
                f'    "color": {{ "r": {r}, "g": {g}, "b": {b}, "a": {a} }},\n'
                f'    "tile": [{api_tiles[0]}, {api_tiles[1]}],\n'
                f'    "pixel": [{abs_x}, {abs_y}],\n'
                f'    "season": 0,\n'
                f'    "colorIdx": {color_idx}\n'
                f'}});'
            )
            commands.append(cmd)
            counter += 1

        return "\n".join(commands)

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

    def compare_image(self, path: str, threshold: float = 0.0) -> bool:
        """
        Compares two images and returns True if they are similar within a certain threshold.

        Args:
            path: Base path for the images
            threshold: Similarity threshold (lower is more strict)

        Returns:
            bool: True if images are similar, False otherwise
        """
        # Load images with alpha channel to consider transparency differences
        good = cv2.imread(f"{path}good.png", cv2.IMREAD_UNCHANGED)
        new = cv2.imread(f"{path}new.png", cv2.IMREAD_UNCHANGED)
        original = cv2.imread(f"{path}original.png", cv2.IMREAD_UNCHANGED)

        # Check if images are loaded successfully
        if good is None or new is None or original is None:
            print(Fore.LIGHTRED_EX + "Error: Could not read one or more image files.")
            return False

        # Ensure images have the same dimensions
        if good.shape != new.shape:
            print(Fore.LIGHTRED_EX + f"Error: Image dimensions do not match. Good: {good.shape}, New: {new.shape}")
            return False # Cannot compare pixel by pixel if dimensions differ

        # Calculate the Mean Squared Error (MSE) across all channels between good and new
        diff = good.astype("float") - new.astype("float")
        err = np.mean(diff ** 2)

        # Calculate the MSE between original and new to check if new image is restored
        diff_2 = original.astype("float") - new.astype("float")
        err_2 = np.mean(diff_2 ** 2)
        if err > threshold and err_2 <= threshold:
            print(Fore.LIGHTGREEN_EX + "La imagen ha sido restaurada. ")
            with open(f"{path}good.png", 'wb') as f:
                f.write(open(f"{path}new.png", 'rb').read())
        elif err <= threshold and err_2 <= threshold:
            print(Fore.LIGHTGREEN_EX + "No se detectaron cambios en los píxeles.")
        elif err <= threshold and err_2 > threshold:
            print(Fore.LIGHTGREEN_EX + "No se detectaron cambios en los píxeles." + Fore.LIGHTYELLOW_EX + " (No original)")

        return bool(err <= threshold) or bool(err_2 <= threshold)

    def get_changed_pixels(self, path: str) -> List[Dict[str, Dict[str, int]]]:
        """
        Locate pixels that differ between two images.

        Args:
            path: Base path for the images

        Returns:
            List of dictionaries with the x, y coordinates and RGBA color of the
            changed pixels in the new image.
        """
        good = cv2.imread(f"{path}good.png", cv2.IMREAD_UNCHANGED)
        new = cv2.imread(f"{path}new.png", cv2.IMREAD_UNCHANGED)

        # Check if images are loaded successfully
        if good is None or new is None:
            return []

        # Check if good and new have the same dimensions
        if good.shape != new.shape:
            return []

        diff = cv2.absdiff(good, new)
        ys, xs = np.nonzero(np.any(diff != 0, axis=2))

        changed = []
        for x, y in zip(xs, ys):
            # Dont check transparent pixels on original image
            # if good[y, x][3] == 0:
            #     continue

            pixel = new[y, x]
            b, g, r, a = pixel
            new_color = (int(r), int(g), int(b), int(a))
            old_color = (int(good[y, x][2]), int(good[y, x][1]), int(good[y, x][0]), int(good[y, x][3]))
            changed.append({
                "x": int(x),
                "y": int(y),
                "new_color": new_color,
                "old_color": old_color
            })
        return changed

    def check_change(self, api_image: str, coords: Tuple[int, int, int, int], path: str) -> None:
        """
        Downloads the new image and checks for changes against the last image.

        Args:
            api_image: URL of the API image
            coords: Coordinates for cropping the image
            path: Base path for saving images
        """
        try:
            self.driver.get(api_image)
        except TimeoutException as e:
            print(Fore.LIGHTRED_EX + f"Error: {e}\n\nWaiting for 5 minutes...")
            time.sleep(5*60) # Wait 5 minutes
            return

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
                    with open(f"{path}new.png", 'wb') as file:
                        file.write(image_data)
                    break

        # Crop the image
        self.crop_image(f"{path}new.png", coords)

        # Check if good image exists
        if not os.path.exists(f"{path}good.png"):
            print(Fore.LIGHTYELLOW_EX + "No se encontró la imagen buena, guardando la nueva imagen como buena.")
            with open(f"{path}original.png", 'wb') as f:
                f.write(open(f"{path}new.png", 'rb').read())
            with open(f"{path}good.png", 'wb') as f:
                f.write(open(f"{path}new.png", 'rb').read())
            return

        # Check for changes
        if not self.compare_image(path):
            changed = self.get_changed_pixels(path)
            print(Fore.LIGHTRED_EX + f"¡ALERTA! Han cambiado {len(changed)} píxeles!!! :<")
            for pixel in changed:
                new_color_name, new_color_id = get_color_id(pixel['new_color'])
                old_color_name, old_color_id = get_color_id(pixel['old_color'])
                print(Fore.LIGHTRED_EX + f"    Pixel cambiado en X={coords[0] + int(str(pixel['x']))}, Y={coords[1] + int(str(pixel['y']))} de {old_color_name}(id: {old_color_id}) a {new_color_name}(id: {new_color_id})")
            self.send_alert(
                f"# ¡ALERTA! Han cambiado {len(changed)} píxeles!!! :< (Antes, después)\n\n## Comando para arreglar los píxeles:\n",
                self.generate_command(changed, coords, api_image),
                f"{path}good.png",
                f"{path}new.png"
            )
            # Replace the new image with the good image
            with open(f"{path}good.png", 'wb') as f:
                f.write(open(f"{path}new.png", 'rb').read())

    def send_alert(self, message: str, command: str, image_path1: str, image_path2: str) -> None:
        """
        Sends an alert message with attached images to a Discord webhook.

        Args:
            message: The alert message to send.
            image_path1: Path to the first image to attach.
            image_path2: Path to the second image to attach.
        """
        discord_webhook_url = arts_data["discord_webhook_url"]
        files = {}

        # If message is too long, create a file and upload it
        if len(message + command) > 2000:
            with open("data/command.js", "w") as f:
                f.write(command)
            payload = {"content": message}
            files["file3"] = (os.path.basename("data/command.js"), open("data/command.js", "rb"))
        else:
            payload = {"content": message + f"```js\n{command}\n```"}

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
                wplace.check_change(api_image, coords, path)
                time.sleep(5)
        except KeyboardInterrupt:
            print("Detected Ctrl + C")
            break
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(arts_data["cooldown"])
        print()


if __name__ == "__main__":
    # Read data config
    with open('data/arts.json') as f:
        arts_data = json.load(f)
    main(arts_data)
