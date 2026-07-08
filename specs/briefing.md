# Sync mode

The propeller-engine can run in the sync mode. That means that `{"command": "loop-start"}` and `{"command": "loop-stop"}` in not allowed.
Add the new value `sync` to the `-s` parameter. If this value is set py-propeller lib will not send the loop start and stop command to the socket.

