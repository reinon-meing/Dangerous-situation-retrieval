#!/bin/bash
# 严格对比 U 盘 (/mnt/usb_view) 与 /root/USB：条目清单(含类型)、文件大小、全量 sha256
export LC_ALL=C
A=/mnt/usb_view; B=/root/USB; O=/root/usb_compare
rm -rf "$O"; mkdir -p "$O"
echo "[start] $(date +%T)"
for side in A B; do
  dir=${!side}
  ( cd "$dir" && find . -mindepth 1 -printf "%y %p\n" | sort > "$O/$side.entries"
    find . -type f -printf "%s %p\n" | sort -k2 > "$O/$side.sizes" )
done
echo "[list] A=$(wc -l < $O/A.entries) 条目  B=$(wc -l < $O/B.entries) 条目"
# 两边并行算哈希（不同设备，互不抢 IO）
( cd "$A" && find . -type f -print0 | sort -z | xargs -0 sha256sum > "$O/A.sha256" ) &
( cd "$B" && find . -type f -print0 | sort -z | xargs -0 -P4 -n 50 sha256sum | sort -k2 > "$O/B.sha256" ) &
wait
sort -k2 -o "$O/A.sha256" "$O/A.sha256"
echo "[hashed] $(date +%T)  A=$(wc -l < $O/A.sha256) 文件  B=$(wc -l < $O/B.sha256) 文件"
echo; echo "===== 1. 条目清单差异（< 仅 U 盘有，> 仅 ~/USB 有）====="
diff "$O/A.entries" "$O/B.entries" && echo "(无差异)"
echo; echo "===== 2. 文件大小差异 ====="
diff "$O/A.sizes" "$O/B.sizes" && echo "(无差异)"
echo; echo "===== 3. sha256 差异 ====="
diff "$O/A.sha256" "$O/B.sha256" && echo "(无差异)"
echo; echo "===== 4. U 盘自身 vs MANIFEST.sha256 ====="
sed "s#  #  ./#" "$A/MANIFEST.sha256" | sort -k2 > "$O/manifest.norm"
join -1 2 -2 2 -o 1.1,2.1,0 "$O/manifest.norm" "$O/A.sha256" | awk "\$1!=\$2{print \"不一致:\", \$3; bad++} END{print \"MANIFEST 中 \" NR \" 个文件已比对，不一致 \" bad+0 \" 个\"}"
echo "MANIFEST 有、U 盘实际没有："; join -v1 -1 2 -2 2 "$O/manifest.norm" "$O/A.sha256" | head; echo "U 盘有、MANIFEST 没列："; join -v2 -1 2 -2 2 "$O/manifest.norm" "$O/A.sha256" | awk "{print \$1}"
echo; echo "[exit] $(date +%T)"
