# T800 Dance Policy Replacement Notes

## Current policy

- Replaced on: 2026-06-02 09:03 Asia/Shanghai
- Source checkpoint:
  `/home/hiyio/engineai/training/whole_body_tracking/logs/rsl_rl/t800_flat/2026-06-01_16-54-59_watchdog_from_38000_20260601_165447_Punch_Swing_L_50hz/model_49500.pt`
- SDK runtime policy:
  `assets/config/t800/rl_dance_example/policies/policy.mnn`
- Checkpoint copy kept at:
  `assets/config/t800/rl_dance_example/policies/model_49500_latest.pt`
- Previous runtime policy backup:
  `assets/config/t800/rl_dance_example/policies/policy.mnn.bak_20260602_090318`

The T800 `dance` motion loads `policy_file` from
`assets/config/t800/rl_dance_example/default.yaml`. The SDK runner uses MNN,
so a `.pt` checkpoint must be exported to `policy.onnx` and converted to
`policy.mnn` before deployment.

## Export this policy again

Run from `/home/hiyio/engineai/training/whole_body_tracking`:

```bash
env ACCEPT_EULA=Y OMNI_KIT_ACCEPT_EULA=YES PYTHONUNBUFFERED=1 \
  PYTHONPATH=/home/hiyio/engineai/training/whole_body_tracking/source/whole_body_tracking \
  /home/hiyio/anaconda3/envs/env_isaacsim51/bin/python scripts/rsl_rl/play.py \
  --task=Tracking-Flat-T800-v0 \
  --num_envs=1 \
  --headless \
  --export_only \
  --load_run=2026-06-01_16-54-59_watchdog_from_38000_20260601_165447_Punch_Swing_L_50hz \
  --checkpoint=model_49500.pt \
  --motion_file=/home/hiyio/engineai/third_party/engineai_robotics_native_sdk/assets/config/t800/rl_dance_example/trajectories/Punch_Swing_L_50hz.npz \
  --device=cpu \
  --kit_args "--portable --no-window" \
  agent.device=cpu env.sim.device=cpu
```

Then convert ONNX to MNN:

```bash
/home/hiyio/anaconda3/bin/mnnconvert \
  -f ONNX \
  --modelFile /home/hiyio/engineai/training/whole_body_tracking/logs/rsl_rl/t800_flat/2026-06-01_16-54-59_watchdog_from_38000_20260601_165447_Punch_Swing_L_50hz/exported/policy.onnx \
  --MNNModel /home/hiyio/engineai/training/whole_body_tracking/logs/rsl_rl/t800_flat/2026-06-01_16-54-59_watchdog_from_38000_20260601_165447_Punch_Swing_L_50hz/exported/policy.mnn \
  --bizCode MNN
```

Expected converter summary:

```text
inputTensors : [ obs, ]
outputTensors: [ actions, ]
Converted Success!
```

## Replace with a new checkpoint

1. Export the new checkpoint with `play.py --export_only`.
2. Convert the exported `policy.onnx` to `policy.mnn` with `mnnconvert`.
3. Back up the current SDK policy:

```bash
cp assets/config/t800/rl_dance_example/policies/policy.mnn \
  assets/config/t800/rl_dance_example/policies/policy.mnn.bak_$(date +%Y%m%d_%H%M%S)
```

4. Copy the new MNN over the runtime policy:

```bash
cp /path/to/new/exported/policy.mnn \
  assets/config/t800/rl_dance_example/policies/policy.mnn
```

5. Optionally keep the source checkpoint beside it:

```bash
cp /path/to/model_xxxxx.pt \
  assets/config/t800/rl_dance_example/policies/model_xxxxx.pt
```

6. Start simulation from the SDK root:

```bash
./scripts/run_mujoco.sh t800
```

Switch to `pd_stand` with `LB + A`, then to `dance` with `RB + B`.
Use `LB + RB` for the emergency fallback to `passive`.
