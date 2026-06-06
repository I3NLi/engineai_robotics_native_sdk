# SDK Runtime Run

Runtime id:
`container_sdk_run_20260606_123719_ground_infinite_model74499`

## Purpose

Validate the SDK MuJoCo environment after deploying the `model_74499` tracking
policy and changing the visual ground plane to render as infinite.

## Ground Plane

Scene source:

- `assets/resource/environment/ground.xml`

Applied visual ground setting:

```xml
<geom name="floor" size="0 0 0.125" type="plane" material="groundplane" conaffinity="7" condim="3" friction="1.0"/>
```

`ground_snippet.txt` captures the loaded XML snippet for this run.

## Components

Logs in this directory:

- `mujoco.log`: MuJoCo simulator startup and physics-loop messages.
- `executor.log`: SDK executor, motion transitions, policy loads, trajectory
  switches.
- `virtual_gamepad.log`: PyQt virtual gamepad process log.
- `ground_snippet.txt`: ground XML snippet captured before relaunch.

Expected processes for this run:

- `./engineai_robotics_simulation_mujoco t800`
- `./src_executor t800`
- `python3 tools/virtual_gamepad/virtual_gamepad.py`

## Validation Summary

Observed:

- MuJoCo 3.2.3 started with robot `t800`.
- SDK active mode was `sim`.
- Executor registered the virtual gamepad input adapter.
- Executor loaded `rl_dance_example/policies/policy.mnn`.
- Policy hash matched the exported `model_74499` MNN:
  `2e39f816cfd83377c084bf6a143e0eeb0b4d812061ab626181838bf649ff2caf`.
- Manual virtual-gamepad interaction entered `dance` and switched between
  punch, kick-turn, riot-combo, and victory trajectories.

The physical gamepad driver may report initialization failure when no USB
gamepad is attached. The virtual gamepad path is the expected input path for
this validation run.

## Operator Notes

- Do not send default `pd_stand -> dance` pulses on simulator relaunch.
- Keep relaunches passive unless an operator explicitly requests a state switch
  or trajectory-selection pulse.
- Direct `X/Y/B/A` input inside `dance` may feel smoother than the UI's
  `Dance Motion Switch` pulse buttons because it does not force pre/post
  release frames.

## Next Milestone

The current tracking policy still has continuation-training potential, but the
next planned project step is fall recovery / get-up behavior. Treat this runtime
run as a deployment validation reference for the current tracking stack, not as
the end of policy development.
