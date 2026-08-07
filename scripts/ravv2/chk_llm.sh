ROOT=/root/ravv2/rootfs
mount -o bind /proc /proc 2>/dev/null || true
mount -o bind /dev /dev 2>/dev/null || true
mount -o bind /run /run 2>/dev/null || true
cp /etc/resolv.conf /etc/resolv.conf.bak 2>/dev/null
printf 'nameserver 1.1.1.1\n' > /etc/resolv.conf
chroot  pacman -Q | grep -iE 'llama|ggml'
chroot  bash -lc 'command -v llama-cli llama-server llama-gguf 2>/dev/null; ls /usr/bin/ 2>/dev/null | grep llama'
mv /etc/resolv.conf.bak /etc/resolv.conf 2>/dev/null
umount /run 2>/dev/null; umount /dev 2>/dev/null; umount /proc 2>/dev/null
