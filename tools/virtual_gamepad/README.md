# visualization

PyQt6-based visualization and debugging tools for the virtual gamepad workflow. The current toolchain provides:

- LCM connection management
- a virtual gamepad publisher
- a lightweight message diagnostic script

## Dependencies

- Python 3.7+
- PyQt6
- lcm

To install the required dependencies, run the following command:
```bash
pip3 install -r requirements.txt
```

## Usage

```bash
python3 tools/virtual_gamepad/virtual_gamepad.py
```

Available widgets/components:

1. `LcmManagerWidget`: connect and disconnect from the target LCM URL.
2. `VirtualGamepadWidget`: publish virtual gamepad messages for debugging.
3. `diagnose_gamepad.py`: basic LCM/message diagnostics for the virtual gamepad channel.

## T800 Dance Macros

The virtual gamepad mirrors the Logitech F710/Xbox button mapping used by the
SDK. For T800 delivery validation, use the state macros first:

| State | Macro |
|:------|:------|
| pd_stand | `LB + A` |
| passive / soft emergency fallback | `LB + RB` |
| walk | `LB + B` |
| walk forward | `LB + B`, then left stick forward for 4 s |
| dance | `LB + A`, then `RB + B` |
| dance punch | `LB + A`, then `RB + B`, then `A` |
| dance punch-fk | `LB + A`, then `RB + B`, then `A + START` |
| dance kick | `LB + A`, then `RB + B`, then `B` |
| dance riot | `LB + A`, then `RB + B`, then `X` |
| dance victory | `LB + A`, then `RB + B`, then `Y` |

The `dance` macro first enters `pd_stand`, then enters the dance state. Use the
motion controls below after the robot is already in `dance`:

| Motion | Macro |
|:-------|:------|
| Pause Toggle | `BACK` |
| Punch | `A` |
| Punch FK | `A + START` |
| Kick Turn | `B` |
| Riot Combo | `X` |
| Victory | `Y` |

## License

This directory is licensed under **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`).
See `LICENSE` for the full license text.

This subdirectory-specific license applies to the virtual gamepad tool itself. Other parts of the repository remain under the repository root license (`LICENSE.txt`) unless explicitly stated otherwise.
