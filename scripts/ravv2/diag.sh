#!/bin/bash
PIDS=$(pgrep -f llama-cli 2>/dev/null || ps aux | grep llama-cli | grep -v grep | awk '{print $2}')
echo "PIDs: $PIDS"
for PID in $PIDS; do
  echo "=== PID $PID ==="
  cat /proc/$PID/wchan 2>/dev/null; echo
  echo "-- fds --"
  ls /proc/$PID/fd 2>/dev/null | wc -l
  ls -la /proc/$PID/fd 2>/dev/null | grep -E "pipe|char|/dev" | head -8
  echo "-- cmdline --"
  tr '\0' ' ' < /proc/$PID/cmdline 2>/dev/null; echo
  echo "-- syscall (wchan2) --"
  grep State /proc/$PID/status 2>/dev/null
done
echo "=== strace disponivel? ==="
command -v strace || echo "sem strace"
echo "=== rootfs dev ==="
ls /root/ravv2/rootfs/dev/ 2>/dev/null | head
echo "=== random ==="
ls -la /root/ravv2/rootfs/dev/random /root/ravv2/rootfs/dev/urandom 2>/dev/null