#!/bin/bash
LEFT="0.269, 1.359, -0.619, 0.946, 0.432, 0.345, 0.654"
RIGHT="-0.184, -1.271, 0.625, -1.133, -0.436, -0.466, -0.658"
ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1
ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$LEFT]}" >/dev/null 2>&1 &
L=$!
ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$RIGHT]}" >/dev/null 2>&1 &
R=$!
sleep 7
kill $L $R 2>/dev/null
sleep 1
python examples/teleavatar_v2/main.py --remote-host 127.0.0.1 --remote-port 8000 --video-decode va --prompt "pick sandbag"
kill $HB 2>/dev/null
