import time

import lcm
from lcm_msgs.data import GamepadKeys


def publish_combo(lcm_handle, indices, frames=10):
    for _ in range(frames):
        msg = GamepadKeys()
        msg.timestamp = int(time.time() * 1_000_000)
        for idx in indices:
            msg.digital_states[idx] = 1
        lcm_handle.publish("virtual_gamepad/gamepad_keys", msg.encode())
        time.sleep(0.05)

    for _ in range(4):
        msg = GamepadKeys()
        msg.timestamp = int(time.time() * 1_000_000)
        lcm_handle.publish("virtual_gamepad/gamepad_keys", msg.encode())
        time.sleep(0.05)


def main():
    lcm_handle = lcm.LCM("udpm://239.255.76.67:7667?ttl=0")
    publish_combo(lcm_handle, [0, 2])  # LB + A: pd_stand
    time.sleep(1.0)
    publish_combo(lcm_handle, [1, 3])  # RB + B: dance
    print("sent pd_stand then dance pulses")


if __name__ == "__main__":
    main()
