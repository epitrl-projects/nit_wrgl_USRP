
#!/bin/bash
tmux kill-server
# Start a new tmux session named 'my_session'
tmux new-session -d -s my_session

# Split the window vertically and run command2

tmux send-keys -t my_session 'mavproxy.py --master=/dev/serial/by-id/usb-Hex_ProfiCNC_CubeOrange_1E0045001251313132383631-if00  --baud=921600 --aircraft="Quaddy" --console --quadcopter --out=255.255.255.255:2346' C-m

sleep 10
tmux split-window -v
# Run command1 in the first window
tmux send-keys -t my_session 'python /home/pi/Desktop/project/final_tests/DONE_SIDE.py' C-m


# Attach to the tmux session
tmux attach-session -t my_session
