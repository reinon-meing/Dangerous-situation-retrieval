#!/bin/bash
# 用法: /root/jogtest.sh <vx> <vy> <wz> <秒> [坡秒]   例: /root/jogtest.sh 0.03 0 0 0.5
cd /root/USB/deploy || exit 1
export OPENPI_DIR=$(pwd)/client/openpi
VX=${1:-0}; VY=${2:-0}; WZ=${3:-0}; SEC=${4:-0.5}; RAMP=${5:-0.3}
pos3() { tr -d '\r' | awk '/^position:/{f=1;next} /^velocity:/{f=0} f&&/^- /{printf "%s ", $2} END{print ""}'; }
read_pos() { client/run_client.sh exec timeout 5 ros2 topic echo --once /chassis/joint_states 2>/dev/null | pos3; }

A=$(read_pos)
[ "$(echo $A | wc -w)" -ge 3 ] || { echo "读不到移动前的 position，不动。"; exit 1; }
echo "移动前: $A"
read -p "vx=$VX vy=$VY wz=$WZ 持续${SEC}秒。急停就位、四周有空地？回车继续，Ctrl+C 放弃 " _
client/run_client.sh exec python examples/teleavatar_v2/jog.py --vx $VX --vy $VY --wz $WZ --seconds $SEC --ramp $RAMP 2>&1 | grep -E "plan|subscriber|zero velocity|ERROR|WARNING|nobody"
sleep 1
B=$(read_pos)
echo "移动后: $B"
awk -v a="$A" -v b="$B" 'BEGIN{n=split(a,x," ");m=split(b,y," ");if(n<3||m<3){print "读数缺失";exit} d1=y[1]-x[1];d2=y[2]-x[2];d3=y[3]-x[3];printf "变化: %+.3f %+.3f %+.3f 三者之和: %+.3f\n",d1,d2,d3,d1+d2+d3}'
