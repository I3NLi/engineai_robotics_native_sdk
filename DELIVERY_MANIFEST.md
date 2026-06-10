# EngineAI Native SDK Delivery

This branch is generated automatically by GitHub Actions.

- Source repository: I3NLi/engineai_robotics_native_sdk
- Source branch: main
- Source commit: 5f18b56e58a7af00365f44694e8d45bf3fbe3fd9
- Delivery branch: delivery
- Delivery tag: delivery/main/5f18b56e58a7-run27253361762-attempt1
- Workflow run: https://github.com/I3NLi/engineai_robotics_native_sdk/actions/runs/27253361762
- Build type: release
- Runtime hotfix: T800 dance runner binary restored from stable source commit 4f12f545e92ab179f773118680ce4a3120595c9c.

## Included runtime content

- Compiled SDK binaries: `build/_install/bin`, `build/_install/lib`
- MuJoCo runtime binary: `simulation/mujoco/build/engineai_robotics_simulation_mujoco`
- T800 multi-motion dance assets: `assets/config/t800/rl_dance_example`
- T800 policy source: validated dance tracking `policy.mnn`
- Container helper scripts: `docker/`
- Virtual gamepad: `tools/virtual_gamepad`

## Source exclusion policy

The delivery branch intentionally excludes C/C++ source trees and build definitions, including `src/`, `core/`, `cmake/`, `CMakeLists.txt`, installed headers, and MuJoCo source files. Only compiled runtime outputs, assets, scripts, docs, policies, and the Python virtual gamepad are published.

## Packaged T800 policy files

- `copy_policy_here.txt`
- `model_49500_latest.pt`
- `policy.mnn`

- `policy.mnn` sha256: `2e39f816cfd83377c084bf6a143e0eeb0b4d812061ab626181838bf649ff2caf`
