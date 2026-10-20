#!/usr/bin/env bash
set -euo pipefail
data_root="${XDG_DATA_HOME:-$HOME/.local/share}"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
target="$data_root/wattpin/application"
if [[ "${1:-}" == "--uninstall" ]]; then exec bash "$target/uninstall.sh" "${@:2}"; fi
if [[ "${1:-}" != "" && "${1:-}" != "--no-launch" ]]; then echo "Usage: bash Wattpin.run [--no-launch|--uninstall]"; exit 2; fi
if [[ -e "$target" && ! -f "$target/.wattpin-managed" ]]; then echo "Install destination is not a managed Wattpin folder; refusing overwrite."; exit 1; fi
mkdir -p -- "$(dirname -- "$target")"
staging="$(mktemp -d "$(dirname -- "$target")/.wattpin-install-XXXXXX")"
trap 'rm -rf -- "$staging"' EXIT
payload_line="$(awk '/^__WATTPIN_PAYLOAD__$/ {print NR+1; exit}' "$0")"
tail -n +"$payload_line" "$0" | tar -xz -C "$staging"
QT_QPA_PLATFORM=offscreen "$staging/Wattpin" --self-test
if ! QT_QPA_PLATFORM=offscreen "$staging/Wattpin" --quit; then echo "Close Wattpin from its tray menu, then run the installer again."; exit 1; fi
if [[ -e "$target" ]]; then rm -rf -- "$target"; fi
mv -- "$staging" "$target"
trap - EXIT
mkdir -p -- "$data_root/applications" "$config_root/autostart"
# Desktop Exec uses its own quoting rules; generate escaped paths without evaluating them.
desktop_quote() { local path="$1"; path="${path//\\/\\\\}"; path="${path//\"/\\\"}"; path="${path//\$/\\\$}"; path="${path//\`/\\\`}"; path="${path//%/%%}"; printf '"%s"' "$path"; }
executable="$(desktop_quote "$target/Wattpin")"
cat > "$data_root/applications/powerglass.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Wattpin
Comment=Desktop power and session energy monitor
Exec=$executable
Icon=$target/_internal/powerglass/assets/wattpin.svg
Terminal=false
Categories=System;Monitor;
EOF
cp -- "$data_root/applications/powerglass.desktop" "$config_root/autostart/powerglass.desktop"
uninstall_terminal=false
if ! command -v zenity >/dev/null 2>&1; then uninstall_terminal=true; fi
cat > "$data_root/applications/wattpin-uninstall.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Uninstall Wattpin
Exec=bash $(desktop_quote "$target/uninstall.sh")
Icon=$target/_internal/powerglass/assets/wattpin.svg
Terminal=$uninstall_terminal
Categories=System;
EOF
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$data_root/applications" || true; fi
echo "Wattpin installed. Open Wattpin from your application menu. Uninstall using Uninstall Wattpin."
if [[ "${1:-}" != "--no-launch" && -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
  nohup "$target/Wattpin" >/dev/null 2>&1 &
fi
exit 0
__WATTPIN_PAYLOAD__
