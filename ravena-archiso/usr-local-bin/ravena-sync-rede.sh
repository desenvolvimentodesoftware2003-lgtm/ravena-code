#!/bin/bash
# RAVENA - sincroniza perfis WiFi p/ a RAVENA-DATA (persistencia entre boots)
# USO: ravena-sync-rede  (ou alias: rede-sync)
[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"
if command -v sync_network_profiles >/dev/null 2>&1; then
    sync_network_profiles
else
    . /usr/local/bin/ravena-data.sh >/dev/null 2>&1
    sync_network_profiles
fi