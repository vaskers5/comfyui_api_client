import os
import re
import time
import logging
from typing import Tuple, List, Dict, Any, Optional
from .api_helpers import generate_image_by_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_available_lora_by_name(loras_dir: str, name: str) -> Optional[str]:
    """
    Find a LoRA file by name in the specified directory.

    Args:
        loras_dir (str): Directory containing LoRA files.
        name (str): Name of the LoRA to search for.

    Returns:
        Optional[str]: Path to the LoRA file if found, otherwise None.
    """
    for file in os.listdir(loras_dir):
        if name in file:
            return os.path.join(loras_dir, file)
    logger.warning(f"LoRA '{name}' not found in directory: {loras_dir}")
    return None


def extract_and_remove_loras(input_string: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract LoRA references from a prompt string and remove them.

    Args:
        input_string (str): The input prompt string containing LoRA references.

    Returns:
        Tuple[List[Dict[str, Any]], str]: A list of LoRAs with their weights, and the cleaned prompt string.
    """
    pattern = r"<lora:([a-zA-Z0-9\-_.]+):([\d.]+)>"
    matches = re.findall(pattern, input_string)
    loras = [{"name": match[0], "weight": float(match[1])} for match in matches]
    cleaned_string = re.sub(pattern, "", input_string).strip()
    return loras, cleaned_string


def add_loras_to_workflow(workflow: Dict, loras: List[Dict], loras_dir: str) -> Dict:
    """
    Add LoRAs to the workflow configuration.

    Args:
        workflow (dict): The workflow configuration dictionary.
        loras (list[dict]): A list of LoRAs with their weights.
        loras_dir (str): Directory containing LoRA files.

    Returns:
        dict: Updated workflow configuration with LoRAs added.
    """
    key = find_workflow_key(workflow, "Power Lora Loader (rgthree)")
    if key is None:
        logger.error("No 'Power Lora Loader' node found in the workflow.")
        return workflow

    lora_idxes = [int(lora_key.split("_")[-1]) for lora_key in workflow[key]["inputs"] if lora_key.startswith("lora_")]
    last_lora_idx = max(lora_idxes, default=0)

    for lora in loras:
        lora_path = find_available_lora_by_name(loras_dir, lora["name"])
        if lora_path is None:
            logger.warning(f"Skipping LoRA '{lora['name']}' as it was not found.")
            continue

        last_lora_idx += 1
        workflow[key]["inputs"][f"lora_{last_lora_idx}"] = {"on": True, "lora": lora_path, "strength": lora["weight"]}
        logger.info(f"Added LoRA '{lora['name']}' with strength {lora['weight']} to the workflow.")

    return workflow


def find_workflow_key(workflow: Dict, key: str) -> Optional[str]:
    """
    Find a workflow node by its class type.

    Args:
        workflow (dict): The workflow configuration dictionary.
        key (str): The class type of the node to search for.

    Returns:
        Optional[str]: Key of the workflow node if found, otherwise None.
    """
    for workflow_key, workflow_data in workflow.items():
        if workflow_data.get("class_type") == key:
            if key == "CLIPTextEncode" and workflow_data["inputs"].get("text") != "":
                continue
            return workflow_key
    logger.warning(f"No node with class type '{key}' found in the workflow.")
    return None


def text2img(
    positive_prompt: str,
    negative_prompt: str,
    loras_dir: str,
    workflow: Dict,
    width: int = 512,
    height: int = 512,
    seed: int = 42,
    batch_size: int = 1,
    server_addr: str = "127.0.0.1:8188",
) -> Tuple[List, float, Dict]:
    """
    Generate images from text prompts using a workflow.

    Args:
        positive_prompt (str): The positive prompt for generating images.
        negative_prompt (str): The negative prompt for generating images.
        loras_dir (str): Directory containing LoRA files.
        workflow (dict): The workflow configuration dictionary.
        width (int): Width of the generated images (default is 512).
        height (int): Height of the generated images (default is 512).
        seed (int): Seed for random generation (default is 42).
        batch_size (int): Number of images to generate in a batch (default is 1).
        server_addr (str): The server address (default is "127.0.0.1:8188").

    Returns:
        Tuple[List, float, Dict]: List of generated images, execution time, and the updated workflow.
    """
    # Extract LoRAs from the positive prompt
    loras, cleaned_positive_prompt = extract_and_remove_loras(positive_prompt)

    # Update workflow with prompts and parameters
    workflow[find_workflow_key(workflow, "DPRandomGenerator")]["inputs"]["text"] = cleaned_positive_prompt
    workflow[find_workflow_key(workflow, "CLIPTextEncode")]["inputs"]["text"] = negative_prompt
    workflow[find_workflow_key(workflow, "EmptyLatentImage")]["inputs"] = {
        "width": width,
        "height": height,
        "batch_size": batch_size,
    }
    workflow[find_workflow_key(workflow, "Seed (rgthree)")]["inputs"]["seed"] = seed

    # Add LoRAs to the workflow
    workflow = add_loras_to_workflow(workflow, loras, loras_dir)

    # Generate images
    logger.info("Starting image generation...")
    start_time = time.time()
    images = generate_image_by_prompt(workflow, server_addr, save_previews=True)
    end_time = time.time()

    execution_time = end_time - start_time
    logger.info(f"Image generation completed in {execution_time:.2f} seconds.")
    return images, execution_time, workflow
