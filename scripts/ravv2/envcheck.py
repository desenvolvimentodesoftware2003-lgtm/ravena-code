import huggingface_hub

print("hf_hub", huggingface_hub.__version__)
import shutil  # noqa: E402

print("free /root/ravv2:", shutil.disk_usage("/root/ravv2"))
