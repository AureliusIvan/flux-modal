import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import modal

flux = (  # Download image layers to run FLUX_Q8.gguf model
    modal.Image.debian_slim(  #this starts with a basic and supported python version
        python_version="3.10.6"
    )
    .apt_install("git", "nano")  # install git and nano
    .pip_install("comfy-cli")  # install comfy-cli
    .run_commands(  # use comfy-cli to install the ComfyUI repo and its dependencies
        "comfy --skip-prompt install --nvidia",
    )
    # Group all node installations
    .run_commands(
        # gguf node required for q8 model
        "comfy node install https://github.com/city96/ComfyUI-GGUF",
        # XLabs ControlNet node
        "comfy node install https://github.com/XLabs-AI/x-flux-comfyui",
        # install control net requried for above xlabs
        "comfy node install https://github.com/Fannovel16/comfyui_controlnet_aux",
        # CR APPLY lora stack -- useful node -- optional
        "comfy node install https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"
    )
    # Group all model downloads, using the specified secrets
    .run_commands(
        # download the GGUF Q8 model
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q8_0.gguf  --relative-path models/unet",
        # download the vae model required to use with the gguf model
        "comfy --skip-prompt model download --url https://civitai.com/api/download/models/928242 --relative-path models/vae --set-civitai-api-token $CIVITAI_API_TOKEN",
        # download the cliper model required to use with GGUF model
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path models/clip",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors --relative-path models/clip",
        # download the lora anime -- optional you can disbale
        "comfy --skip-prompt model download --url https://civitai.com/api/download/models/716064 --relative-path models/loras --set-civitai-api-token $CIVITAI_API_TOKEN",
        # download controlnet v3 xlabs ai
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-controlnet-depth-v3/resolve/main/flux-depth-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-controlnet-canny-v3/resolve/main/flux-canny-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-controlnet-hed-v3/resolve/main/flux-hed-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
        # xlab loras --optional
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/art_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/anime_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/disney_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/mjv6_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/realism_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/scenery_lora_comfy_converted.safetensors --relative-path models/loras",
        # someloras optional
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/alvdansen/frosting_lane_flux/resolve/main/flux_dev_frostinglane_araminta_k.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --set-hf-api-token $HF_API_TOKEN --url https://huggingface.co/multimodalart/flux-tarot-v1/resolve/main/flux_tarot_v1_lora.safetensors --relative-path models/loras",
        secrets=[modal.Secret.from_name("civitai-api-token")]
    )
)

app = modal.App(name="flux-comfyui", image=flux)
@app.function(
    max_containers=1,
    scaledown_window=30,
    timeout=3200,
    # gpu="a10g", # here you can change the gpu, i recommend either a10g or T4
    gpu="T4",
    secrets=[
        modal.Secret.from_name("civitai-api-token"), 
    ],
)
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
