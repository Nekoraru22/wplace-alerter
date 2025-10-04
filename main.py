import os
import sys
import json
import time
import shutil
import threading

from flask_cors import CORS
from pydantic import ValidationError
from flask import Flask, Blueprint, request, jsonify

from controllers.wplace import WPlace, WPlaceArtInterface
from controllers.colors import Color, color_config


# Load arts data
ARTS_DATA = {}
TIME_BETWEEN_PROJECT_CHECKS = 2
__semaforo = threading.Semaphore(1)

def load_arts_data():
    global ARTS_DATA
    __semaforo.acquire()
    try:
        with open('data/arts.json') as file:
            ARTS_DATA = json.load(file)
    finally:
        __semaforo.release()

def save_arts_data():
    global ARTS_DATA
    __semaforo.acquire()
    try:
        with open('data/arts.json', 'w') as file:
            json.dump(ARTS_DATA, file, indent=4)
    finally:
        __semaforo.release()

load_arts_data()
WPLACE = WPlace(ARTS_DATA)


# Flask app setup
app = Flask(__name__,  static_folder='data/frontend_build/browser', static_url_path='')
data_bp = Blueprint('data', __name__, static_folder='data', static_url_path='/data')
app.register_blueprint(data_bp)
CORS(app)


# Routes
@app.get('/')
def index():
    return app.send_static_file('index.html')


@app.get('/projects')
def list_projects():
    load_arts_data()

    for project in ARTS_DATA["arts"]:
        ARTS_DATA["arts"][project]["name"] = project

    return jsonify(list(ARTS_DATA["arts"].values()))


@app.post('/projects/<name>/check')
def check_project(name):
    load_arts_data()
    if name not in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {name} does not exist."), 400

    # Create folder if it doesn't exist
    path = f"data/{name}/"
    os.makedirs(path, exist_ok=True)

    # Check for changes
    message, response = WPLACE.check_change(name)
    return jsonify(message=message, response=response), 200


@app.post('/projects/check')
def check_all_projects():
    load_arts_data()
    responses = []
    try:
        for i, name in enumerate(ARTS_DATA["arts"]):
            if not ARTS_DATA["arts"][name]["track"]:
                continue

            # Create folder if it doesn't exist
            path = f"data/{name}/"
            os.makedirs(path, exist_ok=True)

            # Check for changes
            _, response = WPLACE.check_change(name)
            responses.append(response)

            # Sleep for 5 seconds between checks to avoid rate limiting
            if i < len(ARTS_DATA["arts"]) - 1:
                time.sleep(TIME_BETWEEN_PROJECT_CHECKS)
        return jsonify(message="All projects checked successfully.", responses=responses), 200
    except Exception as e:
        return jsonify(message=str(e)), 400


@app.put('/projects/<project>/edit')
def edit_project(project):
    load_arts_data()
    if project not in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {project} does not exist."), 404
    try:
        data = request.json
        if not data:
            return jsonify(message="No data provided."), 400
        for key in data:
            if key in ARTS_DATA["arts"][project] and key != "name":
                ARTS_DATA["arts"][project][key] = data[key]

        # Save changes to file
        with open('data/arts.json', 'w') as file:
            json.dump(ARTS_DATA, file, indent=4)
    except Exception as e:
        return jsonify(message=str(e)), 400
    return jsonify(message=f"Project {project} edited successfully."), 200


@app.post('/projects')
def add_project():
    load_arts_data()
    data = request.json

    if not data:
        return jsonify(message="No data provided."), 400
    if "name" not in data:
        return jsonify(message="Project name is required."), 400
    name = data["name"]
    if name in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {name} already exists."), 400

    try:
        # Validate data using Pydantic
        validated_project = WPlaceArtInterface(**data)
        
        # Add project
        ARTS_DATA["arts"][name] = {
            "track": validated_project.track,
            "check_transparent_pixels": validated_project.check_transparent_pixels,
            "last_checked": validated_project.last_checked,
            "griefed": validated_project.griefed,
            "api_image": validated_project.api_image,
            "start_coords": {"x": validated_project.start_coords.x, "y": validated_project.start_coords.y},
            "end_coords": {"x": validated_project.end_coords.x, "y": validated_project.end_coords.y}
        }

        # Save changes to file
        with open('data/arts.json', 'w+') as file:
            json.dump(ARTS_DATA, file, indent=4)
            time.sleep(1)  # Ensure file is written before proceeding

            # Check for changes after adding
            if validated_project.track:
                path = f"data/{name}/"
                os.makedirs(path, exist_ok=True)
                _, response = WPLACE.check_change(name)
                return jsonify(message=f"Project {name} added and checked successfully.", response=response), 200
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error['loc'])
            msg = error['msg']
            errors.append(f"{field}: {msg}")
        
        return jsonify(message="Validation error: " + "; ".join(errors)), 400
    
    except Exception as e:
        return jsonify(message=str(e)), 400
    
    return jsonify(message=f"Project {name} added successfully."), 200


@app.delete('/projects/<project>')
def delete_project(project):
    load_arts_data()
    if project not in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {project} does not exist."), 404
    try:
        del ARTS_DATA["arts"][project]

        # Save changes to file
        with open('data/arts.json', 'w') as file:
            json.dump(ARTS_DATA, file, indent=4)

        # Delete project folder
        path = f"data/{project}/"
        shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        return jsonify(message=str(e)), 400
    return jsonify(message=f"Project {project} deleted successfully."), 200


@app.get('/config/colors')
def get_colors():
    return jsonify([{
        "name": color.name,
        "rgb": color_config.get_rgb(color.name),
        "enabled": color_config.get_bool(color.name)
    } for color in Color])


@app.put('/config/colors')
def update_colors():
    data = request.json
    if not data:
        return jsonify(message="No data provided."), 400
    
    for color_name, enabled in data["colors"].items():
        color_config.set_bool(color_name, enabled)
    color_config.save_config()
    return jsonify(message="Colors updated successfully."), 200


@app.get('/projects/automation')
def get_automation_info():
    load_arts_data()
    return jsonify({
        "discord_webhook": ARTS_DATA["discord_webhook"],
        "cooldown_between_checks": ARTS_DATA["cooldown_between_checks"],
        "automated_checks": ARTS_DATA["automated_checks"]
    }), 200


@app.put('/projects/automation')
def update_automation_info():
    data = request.json
    if not data:
        return jsonify(message="No data provided."), 400

    ARTS_DATA["discord_webhook"] = data.get("discord_webhook", ARTS_DATA["discord_webhook"])
    ARTS_DATA["cooldown_between_checks"] = int(data.get("cooldown_between_checks", ARTS_DATA["cooldown_between_checks"]))

    save_arts_data()
    return jsonify(message="Information updated successfully."), 200


@app.put('/projects/automation/toggle')
def toggle_automation_checks():
    data = request.json
    if not data or "automated_checks" not in data:
        return jsonify(message="No data provided."), 400

    ARTS_DATA["automated_checks"] = data["automated_checks"]
    save_arts_data()
    return jsonify(message=f"Automated checks {'enabled' if data['automated_checks'] else 'disabled'} successfully."), 200


@app.get('/projects/<project>/logs')
def get_project_logs(project):
    load_arts_data()
    if project not in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {project} does not exist."), 404
    log_path = f"data/{project}/changes.log"
    if not os.path.exists(log_path):
        return jsonify(message=f"No logs found for project {project}."), 404
    try:
        with open(log_path, 'r') as file:
            logs = file.read()
        return jsonify(message=logs), 200
    except Exception as e:
        return jsonify(message=str(e)), 400
    

@app.get('/projects/<project>/fix-command')
def get_project_fix_command(project):
    load_arts_data()
    if project not in ARTS_DATA["arts"]:
        return jsonify(message=f"Project {project} does not exist."), 404
    log_path = f"data/{project}/fix_pixels.js"
    if not os.path.exists(log_path):
        return jsonify(message=f"No fix command found for project {project}."), 404
    try:
        with open(log_path, 'r') as file:
            fix_command = file.read()
        return jsonify(message=fix_command), 200
    except Exception as e:
        return jsonify(message=str(e)), 400


def automated_check_loop():
    """
    Loop to perform automated checks based on configuration.
    """
    global ARTS_DATA
    
    while True:
        if ARTS_DATA.get("automated_checks", False):
            load_arts_data()
            cooldown = ARTS_DATA.get("cooldown_between_checks", 300)
            
            try:
                print(f"[AUTOMATION] Starting automated check at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                for i, name in enumerate(ARTS_DATA["arts"]):
                    if not ARTS_DATA["arts"][name]["track"]:
                        continue
                    
                    path = f"data/{name}/"
                    os.makedirs(path, exist_ok=True)
                    
                    WPLACE.check_change(name)
                    
                    if i < len(ARTS_DATA["arts"]) - 1:
                        time.sleep(TIME_BETWEEN_PROJECT_CHECKS)

                print(f"[AUTOMATION] Completed automated check. Checked {len(ARTS_DATA['arts'])} projects.")
            except Exception as e:
                print(f"[AUTOMATION] Error during automated check: {e}")
            finally:
                print(f"[AUTOMATION] Next check in {cooldown} seconds")
                time.sleep(cooldown)
        else:
            time.sleep(10)  # Sleep for a while before checking again


def main(args: list):
    if len(args) == 3 and args[1] == "--check":
        if args[2] == "all":
            return check_all_projects()
        else:
            return check_project(args[2])
    if len(args) == 1:
        print("Starting server...")
        try:
            threading.Thread(target=automated_check_loop, daemon=True).start()
            app.run(host='0.0.0.0', port=5000) # , debug=True
        except KeyboardInterrupt:
            print("Detected Ctrl + C")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage:")
        print("  python main.py                         # Start the server")
        print("  python main.py --check all             # Check all projects for changes")
        print("  python main.py --check <project_name>  # Check a specific project for changes")


if __name__ == "__main__":
    main(sys.argv)
