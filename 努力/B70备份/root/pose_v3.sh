#!/bin/bash
LEFT="0.269, 1.359, -0.619, 0.946, 0.432, 0.345, 0.654"
RIGHT="-0.184, -1.271, 0.625, -1.133, -0.436, -0.466, -0.658"

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1
echo "=== FSM"; timeout 2 ros2 topic echo --once /fsm_state --field data

ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$LEFT]}" >/dev/null 2>&1 &
PUBL=$!
ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$RIGHT]}" >/dev/null 2>&1 &
PUBR=$!
sleep 7

echo "=== 实际到位"
timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*"
timeout 2 ros2 topic echo --once /right_arm/joint_states --field position 2>/dev/null | grep -o "array.*"

kill $PUBL $PUBR $HB 2>/dev/null
