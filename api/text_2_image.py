import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any
from requests_toolbelt import MultipartEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_image(
    input_path: str,
    name: str,
    server_address: str,
    client_id: str = "",
    image_type: str = "input",
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Upload an image to the ComfyUI server.

    Args:
        input_path (str): Path to the image file to upload.
        name (str): The name of the image file.
        server_address (str): The server address (e.g., "127.0.0.1:8188").
        client_id (str): Optional client ID for tracking (default is empty).
        image_type (str): Image type, either "input" or another type (default is "input").
        overwrite (bool): Whether to overwrite an existing image (default is False).

    Returns:
        dict: Response from the server.
    """
    try:
        with open(input_path, 'rb') as file:
            multipart_data = MultipartEncoder(
                fields={
                    'image': (name, file, 'image/png'),
                    'type': image_type,
                    'overwrite': str(overwrite).lower(),
                    'client_id': client_id
                }
            )

            headers = {'Content-Type': multipart_data.content_type}
            url = f"http://{server_address}/upload/image"
            request = urllib.request.Request(url, data=multipart_data, headers=headers)

            with urllib.request.urlopen(request) as response:
                logger.info(f"Image '{name}' uploaded successfully to {server_address}.")
                return json.loads(response.read())
    except Exception as e:
        logger.error(f"Failed to upload image '{name}' to {server_address}: {e}")
        raise


def queue_prompt(prompt: Dict, client_id: str, server_address: str) -> Dict:
    """
    Queue a prompt for execution on the ComfyUI server.

    Args:
        prompt (dict): The prompt configuration.
        client_id (str): The client ID for tracking.
        server_address (str): The server address (e.g., "127.0.0.1:8188").

    Returns:
        dict: Response from the server containing the prompt ID.
    """
    try:
        data = json.dumps({"prompt": prompt, "client_id": client_id}).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        url = f"http://{server_address}/prompt"

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            logger.info(f"Prompt queued successfully: {result}")
            return result
    except Exception as e:
        logger.error(f"Failed to queue prompt on {server_address}: {e}")
        raise


def interrupt_prompt(server_address: str) -> Dict:
    """
    Interrupt the currently running prompt on the ComfyUI server.

    Args:
        server_address (str): The server address (e.g., "127.0.0.1:8188").

    Returns:
        dict: Response from the server.
    """
    try:
        url = f"http://{server_address}/interrupt"
        req = urllib.request.Request(url, data={}.encode('utf-8'))
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            logger.info("Prompt interrupted successfully.")
            return result
    except Exception as e:
        logger.error(f"Failed to interrupt prompt on {server_address}: {e}")
        raise


def get_image(filename: str, subfolder: str, folder_type: str, server_address: str) -> bytes:
    """
    Retrieve an image from the ComfyUI server.

    Args:
        filename (str): The name of the image file.
        subfolder (str): The subfolder where the image is stored.
        folder_type (str): The type of folder (e.g., "input" or "output").
        server_address (str): The server address (e.g., "127.0.0.1:8188").

    Returns:
        bytes: The raw image data.
    """
    try:
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        query_string = urllib.parse.urlencode(data)
        url = f"http://{server_address}/view?{query_string}"

        with urllib.request.urlopen(url) as response:
            logger.info(f"Image '{filename}' retrieved successfully from {server_address}.")
            return response.read()
    except Exception as e:
        logger.error(f"Failed to retrieve image '{filename}' from {server_address}: {e}")
        raise


def get_history(prompt_id: str, server_address: str) -> Dict:
    """
    Retrieve the history of a prompt execution.

    Args:
        prompt_id (str): The unique ID of the prompt.
        server_address (str): The server address (e.g., "127.0.0.1:8188").

    Returns:
        dict: The history of the prompt execution.
    """
    try:
        url = f"http://{server_address}/history/{prompt_id}"
        with urllib.request.urlopen(url) as response:
            history = json.loads(response.read())
            logger.info(f"History for prompt ID '{prompt_id}' retrieved successfully.")
            return history
    except Exception as e:
        logger.error(f"Failed to retrieve history for prompt ID '{prompt_id}' from {server_address}: {e}")
        raise


def get_node_info_by_class(node_class: str, server_address: str) -> Dict:
    """
    Retrieve information about a node class from the ComfyUI server.

    Args:
        node_class (str): The name of the node class.
        server_address (str): The server address (e.g., "127.0.0.1:8188").

    Returns:
        dict: Information about the node class.
    """
    try:
        url = f"http://{server_address}/object_info/{node_class}"
        with urllib.request.urlopen(url) as response:
            info = json.loads(response.read())
            logger.info(f"Node info for class '{node_class}' retrieved successfully.")
            return info
    except Exception as e:
        logger.error(f"Failed to retrieve node info for class '{node_class}' from {server_address}: {e}")
        raise


def clear_comfy_cache(server_address: str, unload_models: bool = False, free_memory: bool = False) -> Dict:
    """
    Clear the cache on the ComfyUI server.

    Args:
        server_address (str): The server address (e.g., "127.0.0.1:8188").
        unload_models (bool): Whether to unload models from memory (default is False).
        free_memory (bool): Whether to free memory (default is False).

    Returns:
        dict: Response from the server.
    """
    try:
        clear_data = {
            "unload_models": unload_models,
            "free_memory": free_memory
        }
        data = json.dumps(clear_data).encode('utf-8')
        url = f"http://{server_address}/free"

        with urllib.request.urlopen(url, data=data) as response:
            result = json.loads(response.read())
            logger.info("ComfyUI cache cleared successfully.")
            return result
    except Exception as e:
        logger.error(f"Failed to clear ComfyUI cache on {server_address}: {e}")
        raise
