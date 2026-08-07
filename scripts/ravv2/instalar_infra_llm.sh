#!/bin/bash
# Instala infra LLM no rootfs Ravena
set -e
ROOT=/root/ravv2/rootfs
D=/mnt/c/Users/DELL/AppData/Local/Temp/opencode/ravena_ops

cp "$D/ravena_data_script.sh" "$ROOT/usr/local/bin/ravena-data.sh"
chmod 755 "$ROOT/usr/local/bin/ravena-data.sh"
cp "$D/ravena-data.service" "$ROOT/etc/systemd/system/ravena-data.service"
cp "$D/llm_script.sh" "$ROOT/usr/local/bin/llm"
chmod 755 "$ROOT/usr/local/bin/llm"

mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true

echo '=== enable ravena-data ==='
chroot $ROOT systemctl enable ravena-data.service 2>&1 | head -3

echo '=== alias llm no .bashrc? ==='
grep -q "alias llm=" "$ROOT/home/ravena/.bashrc" && echo "ja existe" || cat >> "$ROOT/home/ravena/.bashrc" <<'EOF'

# RAVENA LLM
alias llm="/usr/local/bin/llm"
alias specs="/usr/local/bin/llm specs"
alias modelos="llm lista"
EOF
echo "OK alias"

umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM