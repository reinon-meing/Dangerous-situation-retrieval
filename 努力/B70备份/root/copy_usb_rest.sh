#!/bin/bash
SRC=/mnt/usb_view; DST=/root/USB
FILES=(
training/base_model.tar
training/base_model.tar.sha256
deploy/server/openpi-xpu-env_v0.1.0.tar.gz
deploy/server/openpi-xpu-env_v0.1.0.tar.gz.sha256
convert/docker/rosbag2lerobot_0.2.0-20261030.tar
convert/docker/SHA256SUMS
training/openpi-env/dist/openpi-env_v0.1.0.tar.gz
training/openpi-env/dist/openpi-env_v0.1.0.tar.gz.sha256
)
echo "[start] $(date +%T)"
for f in "${FILES[@]}"; do
  mkdir -p "$DST/$(dirname "$f")"
  t0=$(date +%s)
  cp -n --preserve=timestamps "$SRC/$f" "$DST/$f" || { echo "[FAIL cp] $f"; exit 1; }
  echo "[copied] $f  $(du -h "$DST/$f" | cut -f1)  $(( $(date +%s)-t0 ))s"
done
sync
echo "[verify] $(date +%T)"
cd "$DST"
: > /tmp/rest.sha256
for f in "${FILES[@]}"; do grep -F "  $f" "$SRC/MANIFEST.sha256" | awk -v p="$f" "{ if (substr(\$0, 67) == p) print }" >> /tmp/rest.sha256; done
echo "manifest lines: $(wc -l < /tmp/rest.sha256)"
sha256sum -c /tmp/rest.sha256
echo "[exit] $? $(date +%T)"
