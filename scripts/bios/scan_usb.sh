#!/bin/bash
echo "=== lsblk completo ==="
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTLABEL,MODEL 2>/dev/null
echo
echo "=== usb via /proc/partitions ==="
cat /proc/partitions
echo
echo "=== blkid ==="
blkid 2>/dev/null
echo
echo "=== fdisk -l (raw) p/ procurar o SanDisk 114GB ==="
fdisk -l 2>/dev/null | grep -A6 -iE "s[a-z]d.*G" | head -40