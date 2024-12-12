import time
import re
import os

from api.api_helpers import generate_image_by_prompt, load_cache_models



def find_available_lora_by_name(loras_dir: str, name: str) -> str:
    for file in os.listdir(loras_dir):
        if name in file:
            return file
    return None


def extract_and_remove_loras(input_string):
    # Regex pattern to match lora substrings
    pattern = r"<lora:([a-zA-Z0-9\-_.]+):([\d.]+)>"
    
    # Find all matches in the string
    matches = re.findall(pattern, input_string)
    
    # Extract lora names and weights into a list
    loras = [{"name": match[0], "weight": float(match[1])} for match in matches]
    
    # Remove all lora substrings from the input string
    cleaned_string = re.sub(pattern, "", input_string)
    
    # Return the extracted loras and the cleaned string
    return loras, cleaned_string.strip()


def add_loras_to_workflow(workflow, loras):
    key = find_workflow_key(workflow, "Power Lora Loader (rgthree)")
    lora_idxes = [int(key.split('_')[-1]) for key in workflow[key]["inputs"] if key.startswith("lora_")]
    if lora_idxes:
        last_lora_idx = max(lora_idxes)
    else:
        last_lora_idx = 0
    
    for lora in loras:
        lora_path = find_available_lora_by_name("/home/kazanplova/ComfyUI/models/loras", lora["name"])
        if lora_path is None or "ip-adapter" in lora_path:
            # print(f"Lora {lora['name']} not found!")
            continue
        last_lora_idx += 1
        workflow[key]["inputs"][f"lora_{last_lora_idx}"] = {
            "on": True,
            "lora": lora_path,
            "strength": lora["weight"]
        }
    return workflow, last_lora_idx

def find_workflow_key(workflow, key):
    for item in workflow:
        workflow_data = workflow[item]
        if workflow_data["class_type"] == key:
            if workflow_data["class_type"] == "CLIPTextEncode" and workflow_data["inputs"]["text"] != "":
                continue
            return item

def text2img(positive_prompt, negative_prompt, loras, workflow, width, height, **kwargs):

    workflow[find_workflow_key(workflow, "DPRandomGenerator")]["inputs"]["text"] = positive_prompt
    workflow[find_workflow_key(workflow, "CLIPTextEncode")]["inputs"]["text"] = negative_prompt
        

    workflow[find_workflow_key(workflow, "EmptyLatentImage")]["inputs"] = {
        "width": width,
        "height": height,
        "batch_size": 1
    }

    workflow, last_lora_idx = add_loras_to_workflow(workflow, loras)

    workflow[find_workflow_key(workflow, "Seed (rgthree)")]["inputs"]["seed"] = 42

    begin = time.time()
    images = generate_image_by_prompt(workflow, save_previews=True)
    end = time.time()
    return images, end - begin, workflow
