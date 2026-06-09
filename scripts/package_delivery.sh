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
    if [[ -n "${GITHUB_RUN_ID:-}" && -n "${GITHUB_SERVER_URL:-}" && -n "${GITHUB_REPOSITORY:-}" ]]; then
      printf -- '- Workflow run: %s/%s/actions/runs/%s\n' "${GITHUB_SERVER_URL}" "${GITHUB_REPOSITORY}" "${GITHUB_RUN_ID}"
    fi
    printf -- '- Build type: release\n\n'
    printf '## Included runtime content\n\n'
    printf -- '- Compiled SDK binaries: `build/_install/bin`, `build/_install/lib`\n'
    printf -- '- MuJoCo runtime binary: `simulation/mujoco/build/engineai_robotics_simulation_mujoco`\n'
    printf -- '- T800 single-Punch dance assets: `assets/config/t800/rl_dance_example`\n'
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
  require_path "${delivery_dir}/tools/virtual_gamepad/virtual_gamepad.py"
}

verify_t800_single_punch_payload() {
  local dance_dir="${delivery_dir}/assets/config/t800/rl_dance_example"
  local trajectories_dir="${dance_dir}/trajectories"
  local default_config="${dance_dir}/default.yaml"

  require_path "${default_config}"
  require_path "${trajectories_dir}/Punch_Swing_L_50hz.npz"

  if find "${trajectories_dir}" -maxdepth 1 -type f -name '*.npz' ! -name 'Punch_Swing_L_50hz.npz' -print -quit | grep -q .; then
    echo "Unexpected T800 dance trajectory found in delivery payload:" >&2
    find "${trajectories_dir}" -maxdepth 1 -type f -name '*.npz' ! -name 'Punch_Swing_L_50hz.npz' -print >&2
    exit 1
  fi

  if grep -nE '(kick_Turn|riot_combo|victory_50hz|warmup|Punch_Swing_L_fk)' "${default_config}" >/tmp/engineai_delivery_t800_motion_refs.txt; then
    echo "Unexpected T800 dance motion reference found in delivery config:" >&2
    cat /tmp/engineai_delivery_t800_motion_refs.txt >&2
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
verify_t800_single_punch_payload
verify_no_cpp_sources
verify_no_internal_notes

echo "Delivery payload assembled at ${delivery_dir}"
