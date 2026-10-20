#!/usr/bin/env bash
set -euo pipefail
app_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$app_root/.wattpin-managed" ]] || { echo "Wattpin installation marker missing; refusing removal."; exit 1; }
data_root="${XDG_DATA_HOME:-$HOME/.local/share}"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
purge=false
confirmed=false
for option in "$@"; do
  case "$option" in --purge-data) purge=true;; --yes) confirmed=true;; *) echo "Unknown option: $option"; exit 2;; esac
done
if ! "$confirmed"; then
  if command -v zenity >/dev/null 2>&1 && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    zenity --question --title="Uninstall Wattpin" --text="Remove Wattpin? Your settings and power history will be kept." || exit 0
  else
    read -r -p "Uninstall Wattpin and keep history? [y/N] " answer
    [[ "$answer" == [yY] ]] || exit 0
  fi
fi
QT_QPA_PLATFORM=offscreen "$app_root/Wattpin" --quit
for entry in "$data_root/applications/powerglass.desktop" "$data_root/applications/wattpin-uninstall.desktop" "$config_root/autostart/powerglass.desktop"; do
  if [[ -f "$entry" ]] && grep -Fq "$app_root" "$entry"; then
    rm -- "$entry"
  fi
done
# This directory is owned by this installer; user data is stored separately.
rm -rf -- "$app_root"
if "$purge"; then rm -rf -- "$data_root/powerglass"; fi
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$data_root/applications" || true; fi
echo "Wattpin removed."
