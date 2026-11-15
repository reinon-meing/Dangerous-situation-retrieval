#!/bin/bash
# pose_raised.sh —— 摆到「抬高姿态」训练起点（v3/v4 用，代替 zero.py）
# 来源：move_raised 56 条首帧均值
# ⚠️ 已知：j7=0.654 贴软限位 0.7
# 执行：docker exec -i openpi-xpu-client /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/pose_raised.sh

LEFT="0.269, 1.359, -0.619, 0.946, 0.432, 0.345, 0.654"
RIGHT="1.003, -0.184, -1.271, 0.625, -1.133, -0.436, -0.466"

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

sleep 6

echo "=== 实际到位情况"
timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*"
timeout 2 ros2 topic echo --once /right_arm/joint_states --field position 2>/dev/null | grep -o "array.*"

kill $PUBL $PUBR $HB 2>/dev/null
