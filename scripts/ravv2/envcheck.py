import huggingface_hub, sys
print("hf_hub", huggingface_hub.__version__)
import shutil
print("free /root/ravv2:", shutil.disk_usage("/root/ravv2"))