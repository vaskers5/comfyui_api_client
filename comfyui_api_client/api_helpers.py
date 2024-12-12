import json
import io
import os
import uuid
import logging
from typing import List, Dict, Tuple, Optional
from websocket import WebSocket
from PIL import Image
from api.websocket_api import queue_prompt, get_history, get_image, upload_image, clear_comfy_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def open_websocket_connection(server_addr: str) -> Tuple[WebSocket, str, str]:
    """
    Open a websocket connection to the ComfyUI server.

    Args:
        server_addr (str): The address of the server (e.g., "127.0.0.1:8188").

    Returns:
        Tuple[WebSocket, str, str]: A tuple containing the WebSocket object, server address, and client ID.
    """
    client_id = str(uuid.uuid4())
    ws = WebSocket()

    try:
        ws.connect(f"ws://{server_addr}/ws?clientId={client_id}")
        logger.info(f"Connected to WebSocket server at {server_addr}")
        return ws, server_addr, client_id
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket at {server_addr}: {e}")
        raise ConnectionError(f"Could not connect to the server at {server_addr}: {e}")


def generate_image_by_prompt(prompt: Dict, server_addr: str, save_previews: bool = False) -> List[Image.Image]:
    """
    Generate images by a provided prompt.

    Args:
        prompt (dict): The dictionary defining the generation prompt.
        server_addr (str): The server address (e.g., "127.0.0.1:8188").
        save_previews (bool): Whether to save preview images.

    Returns:
        List[Image.Image]: A list of generated images.
    """
    ws, _, client_id = open_websocket_connection(server_addr)
    try:
        prompt_id = queue_prompt(prompt, client_id, server_addr)["prompt_id"]
        track_progress(prompt, ws, prompt_id)
        images_data = get_images(prompt_id, server_addr, save_previews)
        return [Image.open(io.BytesIO(img["image_data"])) for img in images_data]
    finally:
        ws.close()


def load_cache_models(workflow: Dict, server_addr: str) -> None:
    """
    Load models into cache.

    Args:
        workflow (dict): The workflow configuration.
        server_addr (str): The server address (e.g., "127.0.0.1:8188").
    """
    ws, _, client_id = open_websocket_connection(server_addr)
    try:
        prompt_id = queue_prompt(workflow, client_id, server_addr)["prompt_id"]
        track_progress(workflow, ws, prompt_id)
    finally:
        ws.close()


def generate_image_by_prompt_and_image(
    prompt: Dict, server_addr: str, output_path: str, input_path: str, filename: str, save_previews: bool = False
) -> None:
    """
    Generate images using a prompt and an input image.

    Args:
        prompt (dict): The dictionary defining the generation prompt.
        server_addr (str): The server address (e.g., "127.0.0.1:8188").
        output_path (str): Path to save the output images.
        input_path (str): Path to the input image.
        filename (str): Name of the input image file.
        save_previews (bool): Whether to save preview images.
    """
    ws, _, client_id = open_websocket_connection(server_addr)
    try:
        upload_image(input_path, filename, server_addr, client_id)
        prompt_id = queue_prompt(prompt, client_id, server_addr)["prompt_id"]
        track_progress(prompt, ws, prompt_id)
        images = get_images(prompt_id, server_addr, save_previews)
        save_images(images, output_path, save_previews)
    finally:
        ws.close()


def save_images(images: List[Dict], output_path: str, save_previews: bool) -> None:
    """
    Save images to the output path.

    Args:
        images (list[dict]): List of image data dictionaries.
        output_path (str): Path to save the images.
        save_previews (bool): Whether to save preview images.
    """
    for img in images:
        directory = os.path.join(output_path, "temp/") if img["type"] == "temp" and save_previews else output_path
        os.makedirs(directory, exist_ok=True)
        try:
            image = Image.open(io.BytesIO(img["image_data"]))
            image.save(os.path.join(directory, img["file_name"]))
            logger.info(f"Image saved: {os.path.join(directory, img['file_name'])}")
        except Exception as e:
            logger.error(f"Failed to save image {img['file_name']}: {e}")


def track_progress(prompt: Dict, ws: WebSocket, prompt_id: str) -> None:
    """
    Track the execution progress of a prompt.

    Args:
        prompt (dict): The dictionary defining the generation prompt.
        ws (WebSocket): The WebSocket object.
        prompt_id (str): The ID of the prompt being tracked.
    """
    node_ids = list(prompt.keys())
    finished_nodes = set()

    while True:
        try:
            message = ws.recv()
        except Exception as e:
            logger.error(f"Error while receiving WebSocket message: {e}")
            break

        if isinstance(message, str):
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "progress":
                logger.info(f"In K-Sampler -> Step: {data['data']['value']} of {data['data']['max']}")
            elif msg_type == "execution_cached":
                for node in data["data"]["nodes"]:
                    if node not in finished_nodes:
                        finished_nodes.add(node)
                        logger.info(f"Progress: {len(finished_nodes)}/{len(node_ids)} Tasks done")
            elif msg_type == "executing":
                node = data["data"]["node"]
                if node and node not in finished_nodes:
                    finished_nodes.add(node)
                    logger.info(f"Progress: {len(finished_nodes)}/{len(node_ids)} Tasks done")
                if node is None and data["data"]["prompt_id"] == prompt_id:
                    break  # Execution is done


def get_images(prompt_id: str, server_addr: str, allow_preview: bool = False) -> List[Dict]:
    """
    Retrieve generated images using a prompt ID.

    Args:
        prompt_id (str): The unique ID of the prompt.
        server_addr (str): The server address (e.g., "127.0.0.1:8188").
        allow_preview (bool): Whether to allow preview images.

    Returns:
        list[dict]: A list of dictionaries containing image data.
    """
    output_images = []
    history = get_history(prompt_id, server_addr).get(prompt_id, {})
    for node_id, node_output in history.get("outputs", {}).items():
        for image in node_output.get("images", []):
            image_data = None
            if allow_preview and image["type"] == "temp":
                image_data = get_image(image["filename"], image["subfolder"], image["type"], server_addr)
            elif image["type"] == "output":
                image_data = get_image(image["filename"], image["subfolder"], image["type"], server_addr)
            if image_data:
                output_images.append({"image_data": image_data, "file_name": image["filename"], "type": image["type"]})
    return output_images


def clear(server_addr: str, unload_models: bool = False, free_memory: bool = False) -> None:
    """
    Clear the ComfyUI cache.

    Args:
        server_addr (str): The server address (e.g., "127.0.0.1:8188").
        unload_models (bool): Whether to unload models from memory.
        free_memory (bool): Whether to free memory.
    """
    try:
        clear_comfy_cache(server_addr, unload_models, free_memory)
        logger.info("Successfully cleared ComfyUI cache.")
    except Exception as e:
        logger.error(f"Failed to clear ComfyUI cache: {e}")
