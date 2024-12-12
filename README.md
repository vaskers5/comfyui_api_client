# comfyui-api-client

A Python API client for ComfyUI, allowing image generation via WebSocket and HTTP requests.

## Installation

You can install `comfyui-api-client` using pip:

```bash
pip install comfyui-api-client
```

This will install the package and its dependencies: Pillow, websocket-client, and requests-toolbelt.

## Usage

This API client interacts with a running ComfyUI server. Ensure your server is running and accessible, usually at `127.0.0.1:8188` if running locally.  You may need to adjust the `server_address` within the client code if your server is running at a different address.  The client communicates with the `/ws` endpoint of your ComfyUI server.

### Basic Example (Text to Image)

This example demonstrates basic text-to-image generation using the `text2img` function.  More detailed examples and usage instructions will be added in future updates.  This assumes you have a basic understanding of ComfyUI workflows and how to structure prompts and parameters. For more advanced usage, refer to the `basic_api.py` example provided in the repository.

```python
from comfyui_api_client import text2img

# Example usage (replace with your actual prompt and parameters)
prompt = "A majestic dragon flying through the clouds."
parameters = {
    # ... your ComfyUI parameters ...
}

try:
    images = text2img(prompt, parameters, server_address="127.0.0.1:8188")  # Adjust server address if needed
    if images:
        for i, image in enumerate(images):
            image.save(f"output_{i}.png")
        print("Images generated successfully!")
    else:
        print("Image generation failed or returned no images.")
except Exception as e:
    print(f"An error occurred: {e}")

```



## Development

For development and contribution, clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/comfyui-api-client  # Replace with your repository URL
cd comfyui-api-client
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.