#pragma once

#include <iostream>
#include <optional>
#include <string>
#include <vector>

#include "basic_param/basic_param.h"
#include "parameter/parameter_loader.h"

namespace data {

class RlDanceExampleParam : public BasicParam {
 public:
  RlDanceExampleParam(std::string_view tag = "rl_dance_example") : BasicParam(tag) { num_actions = joint_names.size(); }

  DEFINE_PARAM_SCOPE(scope_);

  std::string LOAD_PARAM(policy_file);
  std::string LOAD_PARAM(trajectory_file_npz);
  std::optional<std::vector<std::string>> LOAD_PARAM(trajectory_files_npz);

  std::vector<std::string> LOAD_PARAM(joint_names);
  Eigen::VectorXd LOAD_PARAM(joint_stiffness);
  Eigen::VectorXd LOAD_PARAM(joint_damping);
  Eigen::VectorXd LOAD_PARAM(default_joint_pos);

  std::vector<std::string> LOAD_PARAM(observation_names);
  std::vector<int> LOAD_PARAM(observation_history_lengths);
  Eigen::VectorXd LOAD_PARAM(action_scale);
  bool LOAD_PARAM(resident_control);
  int LOAD_PARAM_DEFAULT(trajectory_switch_blend_steps, 25);

  int num_actions;
};

}  // namespace data
