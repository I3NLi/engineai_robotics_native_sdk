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
| dance | `RB + B` |

After entering `dance`, this delivery exposes the validated multi-motion set:

| Motion | Macro |
|:-------|:------|
| Pause Toggle | `BACK` |
| Punch | `A` |
| Victory | `Y` |
| Kick Turn 0.5x | `B` |
| Kick Turn 0.6x | `B + D-pad Up` |
| Kick Turn 0.7x | `B + D-pad Left` |
| Kick Turn 0.8x | `B + D-pad Right` |
| Kick Turn 0.9x | `B + D-pad Down` |
| Kick Turn 1.0x | `B + START` |
| Riot Combo 0.5x | `X` |
| Riot Combo 0.6x | `X + D-pad Up` |
| Riot Combo 0.7x | `X + D-pad Left` |
| Riot Combo 0.8x | `X + D-pad Right` |
| Riot Combo 0.9x | `X + D-pad Down` |
| Riot Combo 1.0x | `X + START` |

## License

This directory is licensed under **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`).
See `LICENSE` for the full license text.

This subdirectory-specific license applies to the virtual gamepad tool itself. Other parts of the repository remain under the repository root license (`LICENSE.txt`) unless explicitly stated otherwise.
