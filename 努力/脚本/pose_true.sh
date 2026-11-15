#!/bin/bash
# pose_true.sh —— 真实复位点（2026-11-15 15:30 现场实测记录）
#
# 来源：由现场操作人员确认，这组角度才是这台机器人真正的复位/起手姿态。
# 记录时的实测读数（原始 16 位精度）：
#   左：[0.3370037078857422, 1.2944984436035156, -0.815375804901123,
#        0.9039812088012695, 0.5149903297424316, 0.30745744705200195, 0.6504063606262207]
#   右：[-0.2092599868774414, -1.1257166862487793, 0.7904319763183594,
#        -1.1709837913513184, -0.5069499015808105, -0.4743356704711914, -0.6285548210144043]
#
# 执行：
#   docker exec -i openpi-xpu-client \
#     /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/pose_true.sh

LEFT="0.3370, 1.2945, -0.8154, 0.9040, 0.5150, 0.3075, 0.6504"
RIGHT="-0.2093, -1.1257, 0.7904, -1.1710, -0.5070, -0.4743, -0.6286"

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1

echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data

echo "=== 摆位：左臂 [$LEFT]"
ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState \
  "{position: [$LEFT]}" >/dev/null 2>&1 &
PUBL=$!

echo "=== 摆位：右臂 [$RIGHT]"
ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState \
  "{position: [$RIGHT]}" >/dev/null 2>&1 &
PUBR=$!

sleep 7

echo "=== 实际到位情况"
timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*"
timeout 2 ros2 topic echo --once /right_arm/joint_states --field position 2>/dev/null | grep -o "array.*"

kill $PUBL $PUBR $HB 2>/dev/null
