import os
import re
import cv2
import json
import time
import base64
import requests
import numpy as np

from PIL import Image
from textwrap import dedent
from colorama import Fore, init
from deprecated import deprecated
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field

from controllers.colors import get_color_id

init(autoreset=True)


Pixel = Dict[str, Dict[str, int]]

class Position(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)

class WPlaceArtInterface(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, pattern=r'^[a-zA-Z0-9_\- ]+$')
    track: bool
    check_transparent_pixels: bool
    last_checked: str = ""
    griefed: bool = False
    api_image: str = Field(..., pattern=r'^https://backend\.wplace\.live/files/s0/tiles/\d+/\d+\.png$')
    start_coords: Position
    end_coords: Position


class WPlace:

    def __init__(self, arts_data: Dict):
        self.session = requests.Session()
        self.timeout = 10
        self.arts_data = arts_data

    
    def __del__(self):
        self.session.close()

    
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


    def generate_command(self, pixels: list, coords: Tuple[int, int, int, int], path: str, api_image: str) -> Tuple[str, str]:
        """
        Generate a compact js command to fix the pixels

        Args:
            pixels: List of pixels to fix
            coords: (start_x, start_y, end_x, end_y) coordinates of the image
            path: The path to save the generated command
            api_image: The API image URL

        Returns:
            The generated js command
        """
        api_tiles = self.get_tiles_from_api_url(api_image)

        # Compact data structure: only essential info
        compact_data = []
        skip_logs = ""

        counter = 1
        for pixel in pixels:
            # Pixel absolute position
            abs_x = coords[0] + pixel['x']
            abs_y = coords[1] + pixel['y']

            # Color
            r, g, b, a = pixel["old_color"]
            _, color_idx, owned = get_color_id(pixel["old_color"])

            # Avoid paid color pixels
            if color_idx == None:
                if pixel["old_color"][3] != 0:
                    skip_logs += f"⚠️ Skipping pixel {counter}/{len(pixels)}: {pixel} for being an unknown color\n"
                counter += 1
                continue
            elif not owned:
                skip_logs += f"⚠️ Skipping pixel {counter}/{len(pixels)}: {pixel} for being a paid color ({color_idx})\n"
                counter += 1
                continue

            # Store only: [x, y, r, g, b, a, colorIdx]
            compact_data.append([abs_x, abs_y, r, g, b, a, color_idx])
            counter += 1

        # Generate the JS file with data + reconstruction code
        js_content = dedent(f"""
            function pixelsToLatLng(x, y) {{
                return data.ctx.crosshair.gm.pixelsToLatLon(x, y, 11);
            }}
            function moveTo(x, y) {{
                const [lat, lng] = pixelsToLatLng(x, y);
                data.ctx.map.flyTo({{
                    center: {{ lat, lng }},
                    zoom: 14
                }})
            }}
            const pixelData = {json.dumps(compact_data)};
            const tiles = {json.dumps(api_tiles)};
            const t0 = tiles[0];
            const t1 = tiles[1];
            const charges = Math.trunc(data.user.charges);
            moveTo(t0*1000 + pixelData[0][0], t1*1000 + pixelData[0][1]);
            // data.ctx.map.showTileBoundaries = true;
            setTimeout(() => {{
                pixelData.slice(0, charges).forEach(p => {{
                    o.set(`t=(${{t0}},${{t1}});p=(${{p[0]}},${{p[1]}});s=0`, {{
                        "color": {{ "r": p[2], "g": p[3], "b": p[4], "a": p[5] }},
                        "tile": tiles,
                        "pixel": [p[0], p[1]],
                        "season": data.ctx.season,
                        "colorIdx": p[6]
                    }});
                }});
                document.querySelector('button.btn-lg.relative').__click();
            }}, 3000);
        """).strip()

        # Save command to file
        with open(f"{path}/fix_pixels.js", "w") as f:
            f.write(js_content)

        return js_content, skip_logs

    
    def crop_image(self, image_path: str, crop_box: Tuple[int, int, int, int]) -> None:
        """
        Crop an image and save the result.
        
        Args:
            image_path: Path to the input image
            crop_box: (left, top, right, bottom) coordinates for cropping
        """
        image = Image.open(image_path)
        cropped_image = image.crop(crop_box)
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
        new = cv2.imread(f"{path}new.png", cv2.IMREAD_UNCHANGED)
        original = cv2.imread(f"{path}original.png", cv2.IMREAD_UNCHANGED)

        # Check if images are loaded successfully
        if original is None or new is None:
            print(Fore.LIGHTRED_EX + "Error: Could not read one or more image files.")
            raise ValueError("Error: Could not read one or more image files.")
        
        # Check if original and new have the same dimensions
        if original.shape != new.shape:
            print(Fore.LIGHTRED_EX + "Error: Images have different dimensions.")
            raise ValueError(f"Error: Images have different dimensions. Original dimensions: {original.shape[1]}x{original.shape[0]}, New dimensions: {new.shape[1]}x{new.shape[0]}")

        # Calculate the MSE (Mean Squared Error) between original and new to check if pixels changed
        diff = original.astype("float") - new.astype("float")
        err = np.mean(diff ** 2)
        
        return bool(err <= threshold)


    def get_changed_pixels(self, path: str, project: str) -> List[Dict[str, Dict[str, int]]]:
        """
        Locate pixels that differ between two images.

        Args:
            path: Base path for the images
            project: The project name to check

        Returns:
            List of dictionaries with the x, y coordinates and RGBA color of the
            changed pixels in the new image.
        """
        # Load images with alpha channel to consider transparency differences
        original = cv2.imread(f"{path}original.png", cv2.IMREAD_UNCHANGED)
        new = cv2.imread(f"{path}new.png", cv2.IMREAD_UNCHANGED)

        # Check if images are loaded successfully
        if original is None or new is None:
            raise ValueError("Error: Could not read one or more image files.")
        
        # Find differing pixels
        diff = cv2.absdiff(original, new)
        ys, xs = np.nonzero(np.any(diff != 0, axis=2))

        changed = []
        for x, y in zip(xs, ys):
            pixel = new[y, x]
            b, g, r, a = pixel
            new_color = (int(r), int(g), int(b), int(a))
            old_color = (int(original[y, x][2]), int(original[y, x][1]), int(original[y, x][0]), int(original[y, x][3]))

            # Dont check transparent pixels if configured
            if not self.arts_data["arts"][project]["check_transparent_pixels"] and old_color[3] == 0:
                continue

            # Normalice transparent pixel representation
            if old_color[3] == 0:
                old_color = (0, 0, 0, 0)

            # If both colors are the same, skip
            if new_color == old_color:
                continue

            changed.append({
                "x": int(x),
                "y": int(y),
                "new_color": new_color,
                "old_color": old_color,
            })
        return changed
    

    @deprecated(reason="Selenium method, not used anymore")
    def save_image_from_network_logs(self, path: str) -> None:
        """
        Save the first PNG image found in the network logs to a file.
        
        Args:
            path: The path to save the image
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import TimeoutException
        options = Options()
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.driver = webdriver.Chrome(options=options)

        # Config
        self.driver.set_page_load_timeout(time_to_wait=20) # TimeoutException if page takes too long to load


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
                    image_data = base64.b64decode(response_body["body"])
                    with open(f"{path}new.png", 'wb') as file:
                        file.write(image_data)
                    break

    
    def download_image(self, url: str, output_path: str) -> None:
        """
        Download an image from a URL and save it to a file.

        Args:
            url: The URL of the image to download
            output_path: The path to save the downloaded image
        """
        response = self.session.get(url, timeout=self.timeout, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            if total_size > 0:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            else:
                f.write(response.content)


    def update_project_in_arts_file(self, art: dict, project_name: str, path: str, logs: str) -> None:
        """
        Update the project's last_checked time and griefed status in arts.json file and save logs.

        Args:
            art: The art dictionary to update
            project_name: The name of the project
            path: The path to save logs
            logs: The logs to save
        """
        checked_time = time.strftime('%Y-%m-%d %H:%M:%S')
        art["last_checked"] = checked_time

        try:
            with open('data/arts.json', 'r') as file:
                arts_data = json.load(file)

            if project_name in arts_data["arts"]:
                arts_data["arts"][project_name] = art
                with open('data/arts.json', 'w') as file:
                    json.dump(arts_data, file, indent=4)
            else:
                print(Fore.LIGHTRED_EX + f"Error: Project {project_name} not found in arts.json.")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"Error updating arts.json: {e}")

        # Save log to file
        with open(f"{path}changes.log", 'w+') as f:
            f.write(f"[{checked_time}]\n")
            f.write(logs if logs != "" else "No changes detected.\n")


    def check_change(self, project: str) -> tuple[str, WPlaceArtInterface]:
        """
        Downloads the new image and checks for changes against the last image.

        Args:
            project: The project name to check
        """
        art = self.arts_data["arts"][project]
        api_image = art["api_image"]
        coords = (
            art["start_coords"]["x"], art["start_coords"]["y"], 
            art["end_coords"]["x"], art["end_coords"]["y"]
        )
        path = f"data/{project}/"

        try:
            print(Fore.LIGHTYELLOW_EX + f"Checking art: {Fore.RESET}{project}", end=' -> ')
            self.download_image(api_image, f"{path}new.png")
        except Exception as e:
            raise Exception(Fore.LIGHTRED_EX + f"Error downloading image: {e}")

        # Crop the image
        self.crop_image(f"{path}new.png", coords)

        # Check if original image exists
        if not os.path.exists(f"{path}original.png"):
            with open(f"{path}original.png", 'wb') as f:
                f.write(open(f"{path}new.png", 'rb').read())
            print(Fore.LIGHTYELLOW_EX + "Original image not found, saving new image as original.", end=' -> ')

        # Check for changes
        logs = str()
        message = ""
        if not self.compare_image(path):
            changed = self.get_changed_pixels(path, project)
            if len(changed) == 0:
                if art["griefed"]:
                    message = "Pixels restored to original state."
                    print(Fore.LIGHTCYAN_EX + message)
                    art["griefed"] = False
                else:
                    message = "No changes detected in pixels."
                    print(Fore.LIGHTGREEN_EX + message)

                self.update_project_in_arts_file(art, project, path, logs)
                return message, art
            else:
                print(Fore.LIGHTRED_EX + f"Detected {len(changed)} changed pixels!")
                message = f"Detected {len(changed)} changed pixels!"
                logs += f"Detected {len(changed)} changed pixels!\n"
                art["griefed"] = True

            for pixel in changed:
                new_color_name, new_color_id, _ = get_color_id(pixel['new_color'])
                old_color_name, old_color_id, _ = get_color_id(pixel['old_color'])
                logs += f"Pixel changed at X={coords[0] + int(str(pixel['x']))}, Y={coords[1] + int(str(pixel['y']))} from {old_color_name}(id: {old_color_id}) to {new_color_name}(id: {new_color_id})\n"

            result = self.generate_command(changed, coords, path, api_image)
            command = result[0]
            skip_logs = result[1]
            logs += skip_logs

            if art["track"]:
                self.send_alert(
                    f"# ¡ALERT! {len(changed)} Pixels changed!!! :< (Before, After)\n\n## Command to fix the pixels:\n",
                    command,
                    f"{path}original.png",
                    f"{path}new.png"
                )
        else:
            if art["griefed"]:
                message = "Pixels restored to original state."
                print(Fore.LIGHTCYAN_EX + message)
                art["griefed"] = False
            else:
                message = "No changes detected in pixels."
                print(Fore.LIGHTGREEN_EX + message)
        self.update_project_in_arts_file(art, project, path, logs)

        art["name"] = project
        return message, art

    
    def send_alert(self, message: str, command: str, original_image: str, new_image: str) -> None:
        """
        Sends an alert message with attached images to a Discord webhook.

        Args:
            message: The alert message to send.
            original_image: Path to the first image to attach.
            new_image: Path to the second image to attach.
        """
        discord_webhook = self.arts_data["discord_webhook"]
        files = {}

        # Dont send if no webhook is configured
        if not discord_webhook:
            print(Fore.LIGHTRED_EX + "Error: No Discord webhook URL configured.")
            return

        # If message is too long, create a file and upload it
        if len(message + command) > 2000:
            with open("data/command.js", "w") as f:
                f.write(command)
            payload = {"content": message}
            files["file3"] = (os.path.basename("data/command.js"), open("data/command.js", "rb"))
        else:
            payload = {"content": message + f"```js\n{command}\n```"}

        if original_image and os.path.exists(original_image):
            try:
                files["file1"] = (os.path.basename(original_image), open(original_image, "rb"))
            except IOError:
                print(Fore.LIGHTRED_EX + f"Error: Could not open {original_image} for reading.")

        if new_image and os.path.exists(new_image):
            try:
                files["file2"] = (os.path.basename(new_image), open(new_image, "rb"))
            except IOError:
                print(Fore.LIGHTRED_EX + f"Error: Could not open {new_image} for reading.")

        try:
            response = requests.post(discord_webhook, data=payload, files=files)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print(Fore.LIGHTRED_EX + f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(Fore.LIGHTRED_EX + f"Connection Error: {errc}")
        except requests.exceptions.Timeout as errt:
            print(Fore.LIGHTRED_EX + f"Timeout: {errt}")
        except requests.exceptions.RequestException as err:
            print(Fore.LIGHTRED_EX + f"Error: {err}")
        finally:
            # Ensure files are closed after sending
            for f in files.values():
                f[1].close()

            # Remove temporary command file if created
            if os.path.exists("data/command.js"):
                os.remove("data/command.js")
