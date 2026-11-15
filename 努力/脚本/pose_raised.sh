#!/bin/bash
# pose_raised.sh —— 摆到「new 数据集的训练起点姿态」（抬高后）
#
# 用途：跑模型前用它代替 zero.py，让手臂起点和训练数据一致。
#
# 数据来源：/root/out/move_raised 数据集，56 条 episode 的 observation.state 首帧均值（前 14 维）
#          左右臂各 7 个关节角，单位：弧度
#
# ⚠️ 已知问题：j7 = 0.654，上限 0.7，只剩 0.046 余量（手腕几乎拧到底）
#             下一批录制建议把 j7 收到 0.3~0.4
#
# 执行：
#   docker exec -i openpi-xpu-client \
#     /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/pose_raised.sh

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
