from setuptools import setup, find_packages

setup(
    name="comfyui-api-client",  # Unique name for your package
    version="0.1.0",  # Follow semantic versioning (major.minor.patch)
    author="Kazancev Danil",
    author_email="your.email@example.com",
    description="A Python API client for ComfyUI to generate images through WebSocket and HTTP requests.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",  # Render README in markdown on PyPI
    url="https://github.com/yourusername/comfyui-api-client",  # Link to your project repository
    license="MIT",  # Choose a license (e.g., MIT, Apache, etc.)
    packages=find_packages(),  # Automatically find and include all packages
    install_requires=[
        "Pillow==10.2.0",
        "websocket-client==1.7.0",
        "requests_toolbelt==1.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Minimum Python version requirement
)