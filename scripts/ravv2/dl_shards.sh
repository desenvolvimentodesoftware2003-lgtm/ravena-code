#!/bin/bash
cd /root/ravv2
for f in 01 02; do
  fname="model.safetensors-000${f}-of-00002.safetensors"
  echo "$(date +%H:%M:%S) iniciando $fname" >> /root/ravv2/dl_shards.log
  wget -c -q "https://huggingface.co/Qwen/Qwen3.5-4B/resolve/main/${fname}" \
    -O "/root/ravv2/qwen35_4b_shard${f}.safetensors"
  echo "$(date +%H:%M:%S) done $fname exit=$?" >> /root/ravv2/dl_shards.log
done
echo "$(date +%H:%M:%S) ALL_DONE" >> /root/ravv2/dl_shards.log