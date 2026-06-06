# Runtime Logs

This directory stores SDK/MuJoCo validation runs.

Each significant runtime run should include a local `README.md` describing:

- purpose;
- policy/checkpoint being validated;
- simulator or environment changes;
- expected processes;
- validation result;
- operator notes.

## Current Reference Run

`container_sdk_run_20260606_123719_ground_infinite_model74499`

- Validates the deployed `model_74499` MNN.
- Uses the visual-infinite MuJoCo ground plane:
  `assets/resource/environment/ground.xml`, `size="0 0 0.125"`.
- Includes MuJoCo, executor, and virtual gamepad logs.
- Documents that default `pd_stand -> dance` pulses should not be sent on
  relaunch unless explicitly requested.

## Project Direction

The current tracking stack still has continuation-training potential, but the
next planned project milestone is fall recovery / get-up behavior.
