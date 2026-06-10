#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/package_delivery.sh <delivery_dir>

Assemble the compiled delivery payload after ./build.sh and
./scripts/build_mujoco.sh have completed.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
delivery_dir="${1:-${DELIVERY_DIR:-}}"
readonly t800_delivery_policy_sha256="2e39f816cfd83377c084bf6a143e0eeb0b4d812061ab626181838bf649ff2caf"
readonly t800_delivery_trajectories=(
  "Punch_Swing_L_50hz.npz"
  "kick_Turn_50hz.npz"
  "riot_combo_50hz.npz"
  "victory_50hz.npz"
)

if [[ -z "${delivery_dir}" ]]; then
  usage >&2
  exit 1
fi

require_path() {
  local path="$1"
  if [[ ! -e "${path}" ]]; then
    echo "Required delivery input is missing: ${path}" >&2
    exit 1
  fi
}

copy_dir() {
  local src="$1"
  local dst="$2"

  require_path "${src}"
  mkdir -p "${dst}"
  rsync -a \
    --exclude='**/__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.tmp' \
    --exclude='*.bak_*' \
    --exclude='*_bak_*' \
    --exclude='.DS_Store' \
    --exclude='.pytest_cache/' \
    --exclude='dockers/' \
    "${src}/" "${dst}/"
}

write_manifest() {
  local manifest="${delivery_dir}/DELIVERY_MANIFEST.md"

  {
    printf '# EngineAI Native SDK Delivery\n\n'
    printf 'This branch is generated automatically by GitHub Actions.\n\n'
    printf -- '- Source repository: %s\n' "${GITHUB_REPOSITORY:-unknown}"
    printf -- '- Source branch: %s\n' "${GITHUB_REF_NAME:-unknown}"
    printf -- '- Source commit: %s\n' "${GITHUB_SHA:-$(git -C "${source_dir}" rev-parse HEAD 2>/dev/null || printf unknown)}"
    printf -- '- Delivery branch: %s\n' "${DELIVERY_BRANCH:-delivery}"
    printf -- '- Delivery tag: %s\n' "${DELIVERY_TAG:-untagged}"
    if [[ -n "${GITHUB_RUN_ID:-}" && -n "${GITHUB_SERVER_URL:-}" && -n "${GITHUB_REPOSITORY:-}" ]]; then
      printf -- '- Workflow run: %s/%s/actions/runs/%s\n' "${GITHUB_SERVER_URL}" "${GITHUB_REPOSITORY}" "${GITHUB_RUN_ID}"
    fi
    printf -- '- Build type: release\n\n'
    printf '## Included runtime content\n\n'
    printf -- '- Compiled SDK binaries: `build/_install/bin`, `build/_install/lib`\n'
    printf -- '- MuJoCo runtime binary: `simulation/mujoco/build/engineai_robotics_simulation_mujoco`\n'
    printf -- '- T800 multi-motion dance assets: `assets/config/t800/rl_dance_example`\n'
    printf -- '- T800 policy source: validated dance tracking `policy.mnn`\n'
    printf -- '- Container helper scripts: `docker/`\n'
    printf -- '- Virtual gamepad: `tools/virtual_gamepad`\n\n'
    printf '## Source exclusion policy\n\n'
    printf 'The delivery branch intentionally excludes C/C++ source trees and build definitions, including '
    printf '`src/`, `core/`, `cmake/`, `CMakeLists.txt`, installed headers, and MuJoCo source files. '
    printf 'Only compiled runtime outputs, assets, scripts, docs, policies, and the Python virtual gamepad are published.\n\n'
  } > "${manifest}"

  if [[ -d "${delivery_dir}/assets/config/t800/rl_dance_example/policies" ]]; then
    {
      printf '## Packaged T800 policy files\n\n'
      find "${delivery_dir}/assets/config/t800/rl_dance_example/policies" -maxdepth 1 -type f \
        -printf '- `%f`\n' | sort
      printf '\n'
      printf -- '- `policy.mnn` sha256: `%s`\n' "${t800_delivery_policy_sha256}"
      printf '\n'
    } >> "${manifest}"
  fi
}

verify_no_cpp_sources() {
  cd "${delivery_dir}"

  local forbidden_paths=(
    "./src"
    "./core"
    "./cmake"
    "./CMakeLists.txt"
    "./build.sh"
  )

  for path in "${forbidden_paths[@]}"; do
    if [[ -e "${path}" ]]; then
      echo "Forbidden delivery path found: ${path}" >&2
      exit 1
    fi
  done

  if find . -type f \( \
      -name '*.c' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' -o \
      -name '*.h' -o -name '*.hh' -o -name '*.hpp' -o -name '*.hxx' \
    \) -print -quit | grep -q .; then
    echo "C/C++ source or header files found in delivery payload:" >&2
    find . -type f \( \
      -name '*.c' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' -o \
      -name '*.h' -o -name '*.hh' -o -name '*.hpp' -o -name '*.hxx' \
    \) >&2
    exit 1
  fi
}

verify_required_runtime_payload() {
  require_path "${delivery_dir}/build/_install/bin"
  require_path "${delivery_dir}/build/_install/lib"
  require_path "${delivery_dir}/simulation/mujoco/build/engineai_robotics_simulation_mujoco"
  require_path "${delivery_dir}/simulation/mujoco/build/src/lcm_interface/libsrc_lcm_interface.so"
  require_path "${delivery_dir}/assets/config/t800/rl_dance_example/policies/policy.mnn"
  require_path "${delivery_dir}/assets/config/t800/rl_dance_example/trajectories/Punch_Swing_L_50hz.npz"
  require_path "${delivery_dir}/assets/config/t800/rl_dance_example/trajectories/kick_Turn_50hz.npz"
  require_path "${delivery_dir}/assets/config/t800/rl_dance_example/trajectories/riot_combo_50hz.npz"
  require_path "${delivery_dir}/assets/config/t800/rl_dance_example/trajectories/victory_50hz.npz"
  require_path "${delivery_dir}/tools/virtual_gamepad/virtual_gamepad.py"
}

verify_t800_dance_payload() {
  local dance_dir="${delivery_dir}/assets/config/t800/rl_dance_example"
  local trajectories_dir="${dance_dir}/trajectories"
  local policies_dir="${dance_dir}/policies"
  local default_config="${dance_dir}/default.yaml"
  local policy_file="${dance_dir}/policies/policy.mnn"
  local policy_sha256

  require_path "${default_config}"
  require_path "${policy_file}"

  policy_sha256="$(sha256sum "${policy_file}" | awk '{print $1}')"
  if [[ "${policy_sha256}" != "${t800_delivery_policy_sha256}" ]]; then
    echo "Unexpected T800 delivery policy sha256: ${policy_sha256}" >&2
    echo "Expected: ${t800_delivery_policy_sha256}" >&2
    exit 1
  fi

  for trajectory in "${t800_delivery_trajectories[@]}"; do
    require_path "${trajectories_dir}/${trajectory}"
    if ! grep -Fq "rl_dance_example/trajectories/${trajectory}" "${default_config}"; then
      echo "Expected T800 dance motion reference missing from delivery config: ${trajectory}" >&2
      exit 1
    fi
  done

  while IFS= read -r trajectory_path; do
    local trajectory_name
    trajectory_name="$(basename "${trajectory_path}")"
    case " ${t800_delivery_trajectories[*]} " in
      *" ${trajectory_name} "*) ;;
      *)
        echo "Unexpected T800 dance trajectory found in delivery payload: ${trajectory_name}" >&2
        exit 1
        ;;
    esac
  done < <(find "${trajectories_dir}" -maxdepth 1 -type f -name '*.npz' | sort)

  while IFS= read -r policy_path; do
    local policy_name
    policy_name="$(basename "${policy_path}")"
    case "${policy_name}" in
      "policy.mnn" | "model_49500_latest.pt" | "copy_policy_here.txt") ;;
      *)
        echo "Unexpected T800 policy file found in delivery payload: ${policy_name}" >&2
        exit 1
        ;;
    esac
  done < <(find "${policies_dir}" -maxdepth 1 -type f | sort)

  if ! find "${trajectories_dir}" -maxdepth 1 -type f -name '*.npz' -print -quit | grep -q .; then
    echo "No T800 dance trajectories found in delivery payload" >&2
    exit 1
  fi
}

verify_no_internal_notes() {
  local forbidden_names=(
    "POLICY_REPLACEMENT_T800.md"
    "runtime_logs"
    "verify_logs"
    "package_delivery.sh"
  )

  for name in "${forbidden_names[@]}"; do
    if find "${delivery_dir}" -name "${name}" -print -quit | grep -q .; then
      echo "Internal delivery-only file or directory found: ${name}" >&2
      exit 1
    fi
  done

  if grep -RInE \
      '(/home/hiyio|runtime_logs|container_sdk_run|POLICY_REPLACEMENT|chatgpt|codex|conversation|dialogue|对话|聊天|提示词)' \
      "${delivery_dir}" \
      --exclude-dir=.git \
      --exclude-dir=build \
      --exclude='*.png' \
      --exclude='*.jpg' \
      --exclude='*.dae' \
      --exclude='*.obj' \
      --exclude='*.mnn' \
      --exclude='*.npz' \
      --exclude='*.so' \
      --exclude='*.a' \
      >/tmp/engineai_delivery_internal_notes.txt; then
    echo "Possible internal notes found in delivery payload:" >&2
    cat /tmp/engineai_delivery_internal_notes.txt >&2
    exit 1
  fi
}

copy_runtime_script() {
  local rel_path="$1"

  require_path "${source_dir}/${rel_path}"
  mkdir -p "$(dirname "${delivery_dir}/${rel_path}")"
  cp -a "${source_dir}/${rel_path}" "${delivery_dir}/${rel_path}"
}

rm -rf "${delivery_dir}"
mkdir -p "${delivery_dir}/build/_install"

require_path "${source_dir}/build/_install/bin"
require_path "${source_dir}/build/_install/lib"

copy_dir "${source_dir}/build/_install/bin" "${delivery_dir}/build/_install/bin"
copy_dir "${source_dir}/build/_install/lib" "${delivery_dir}/build/_install/lib"
if [[ -d "${source_dir}/build/_install/share" ]]; then
  copy_dir "${source_dir}/build/_install/share" "${delivery_dir}/build/_install/share"
fi

require_path "${source_dir}/simulation/mujoco/build/engineai_robotics_simulation_mujoco"
require_path "${source_dir}/simulation/mujoco/build/src/lcm_interface/libsrc_lcm_interface.so"
mkdir -p "${delivery_dir}/simulation/mujoco/build/src/lcm_interface"
cp -a "${source_dir}/simulation/mujoco/build/engineai_robotics_simulation_mujoco" \
  "${delivery_dir}/simulation/mujoco/build/"
cp -a "${source_dir}/simulation/mujoco/build/src/lcm_interface/libsrc_lcm_interface.so" \
  "${delivery_dir}/simulation/mujoco/build/src/lcm_interface/"

copy_dir "${source_dir}/assets" "${delivery_dir}/assets"
copy_dir "${source_dir}/docker" "${delivery_dir}/docker"
copy_dir "${source_dir}/docs" "${delivery_dir}/docs"
copy_dir "${source_dir}/tools/virtual_gamepad" "${delivery_dir}/tools/virtual_gamepad"

copy_runtime_script "scripts/env_robot.sh"
copy_runtime_script "scripts/plotjuggler/common_data_display.xml"
copy_runtime_script "scripts/process_dump.sh"
copy_runtime_script "scripts/run_mujoco.sh"
copy_runtime_script "scripts/run_plotjuggler.sh"
copy_runtime_script "scripts/run_robot.sh"
copy_runtime_script "scripts/set_imu_tty.sh"

for file in LICENSE.txt README.md README_CN.md env.sh run.sh install.sh clear.sh; do
  if [[ -f "${source_dir}/${file}" ]]; then
    cp -a "${source_dir}/${file}" "${delivery_dir}/"
  fi
done

find "${delivery_dir}/build/_install/bin" "${delivery_dir}/build/_install/lib" \
  -type f -perm -u+x -exec strip --strip-unneeded {} + 2>/dev/null || true
find "${delivery_dir}/simulation/mujoco/build" \
  -type f -perm -u+x -exec strip --strip-unneeded {} + 2>/dev/null || true

write_manifest
verify_required_runtime_payload
verify_t800_dance_payload
verify_no_cpp_sources
verify_no_internal_notes

echo "Delivery payload assembled at ${delivery_dir}"
