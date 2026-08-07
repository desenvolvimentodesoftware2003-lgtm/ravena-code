#!/bin/bash
# Diagnostico: roda llama-cli no chroot, monitora saida periodicamente
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true

# garante modelo dentro do chroot
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"

echo "### inicio $(date +%T)"
nohup timeout 150 chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 48 -t 4 -ngl 0 --no-mmap --no-display-prompt --no-conversation > /tmp/llm_plot.txt 2>&1 &
PID=$!
echo "PID=$PID"
for i in 1 2 3 4 5 6; do
  sleep 20
  echo "### poll $i ($(date +%T)) bytes=$(wc -c < /tmp/llm_plot.txt)"
  tail -6 /tmp/llm_plot.txt
  kill -0 $PID 2>/dev/null || { echo "processo terminou"; break; }
done
kill -9 $PID 2>/dev/null || true
echo "### stderr/saida final:"
tail -30 /tmp/llm_plot.txt
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM