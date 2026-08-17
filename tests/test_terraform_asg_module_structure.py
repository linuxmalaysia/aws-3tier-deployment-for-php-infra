#!/usr/bin/env python3
"""Structural/regression tests for the ASG Terraform module after it was
split from a single monolithic ``terraform/modules/asg/main.tf`` into five
single-responsibility files:

* ``data.tf``             -- AMI SSM parameter data sources + AMI selection locals
* ``iam.tf``               -- IAM role, policy attachment, instance profile
* ``launch_template.tf``   -- ``aws_launch_template.main``
* ``asg.tf``               -- ``aws_autoscaling_group.main``
* ``scaling_policies.tf``  -- CPU-based scaling policies + CloudWatch alarms

These ``.tf`` files are treated as plain text (regex-based structural
checks), following the dependency-free convention already used throughout
this repository's test suite (e.g.
``tests/test_terraform_ec2_metadata_retrieval.py``). This is a pure
refactor -- no resource arguments changed -- so these tests guard against
regressions introduced by the split itself: that every resource/data
source that used to live in the monolithic ``main.tf`` still exists
exactly once, lives in its expected file, and that the cross-file
references between them (e.g. the launch template referencing the IAM
instance profile, or the ASG referencing the launch template) survived
the move.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_terraform_asg_module_structure
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASG_MODULE_DIR = os.path.join(REPO_ROOT, "terraform", "modules", "asg")

DATA_TF = os.path.join(ASG_MODULE_DIR, "data.tf")
IAM_TF = os.path.join(ASG_MODULE_DIR, "iam.tf")
LAUNCH_TEMPLATE_TF = os.path.join(ASG_MODULE_DIR, "launch_template.tf")
ASG_TF = os.path.join(ASG_MODULE_DIR, "asg.tf")
SCALING_POLICIES_TF = os.path.join(ASG_MODULE_DIR, "scaling_policies.tf")
OLD_MONOLITHIC_MAIN_TF = os.path.join(ASG_MODULE_DIR, "main.tf")

SPLIT_FILES = {
    "data": DATA_TF,
    "iam": IAM_TF,
    "launch_template": LAUNCH_TEMPLATE_TF,
    "asg": ASG_TF,
    "scaling_policies": SCALING_POLICIES_TF,
}

# Every top-level `resource`/`data` block that existed in the pre-split
# main.tf, mapped to the single file it must now live in exclusively.
EXPECTED_BLOCK_LOCATIONS = {
    'data "aws_ssm_parameter" "al2023_x86_64"': "data",
    'data "aws_ssm_parameter" "al2023_arm64"': "data",
    'resource "aws_iam_role" "instance_role"': "iam",
    'resource "aws_iam_role_policy_attachment" "ssm_policy"': "iam",
    'resource "aws_iam_instance_profile" "instance_profile"': "iam",
    'resource "aws_launch_template" "main"': "launch_template",
    'resource "aws_autoscaling_group" "main"': "asg",
    'resource "aws_autoscaling_policy" "scale_out"': "scaling_policies",
    'resource "aws_autoscaling_policy" "scale_in"': "scaling_policies",
    'resource "aws_cloudwatch_metric_alarm" "cpu_high"': "scaling_policies",
    'resource "aws_cloudwatch_metric_alarm" "cpu_low"': "scaling_policies",
}


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_top_level_block(content, header):
    """Extract a single top-level ``resource``/``data`` block starting at
    ``header`` (e.g. ``resource "aws_iam_role" "instance_role" {``) up to
    its unindented closing ``}``.

    A naive ``[^}]*`` scan is unsafe here because these files embed HCL
    string interpolations like ``"${var.environment}-asg-scale-out"``,
    which themselves contain a literal ``}`` character that is *not* the
    end of the block. Instead, the block is considered closed at the next
    ``}`` that starts its own line (column 0), which is how ``tofu fmt``
    always formats a top-level block's closing brace, as opposed to the
    indented closing braces of nested blocks (e.g. ``dimensions = { ... }``)
    or the inline ``}`` from a string interpolation.
    """
    start = content.index(header)
    close_match = re.search(r"\n\}(?=\n|\Z)", content[start:])
    assert close_match is not None, f"Could not locate closing '}}' for {header!r}"
    end = start + close_match.end()
    return content[start:end]


class AsgModuleFileLayoutTestCase(unittest.TestCase):
    """Confirms the monolithic main.tf was fully replaced by the five
    single-responsibility files, with no leftovers and no duplication."""

    @classmethod
    def setUpClass(cls):
        cls.contents = {name: _read(path) for name, path in SPLIT_FILES.items()}

    def test_all_split_files_exist(self):
        for name, path in SPLIT_FILES.items():
            with self.subTest(file=name):
                self.assertTrue(os.path.isfile(path), f"{path} should exist")

    def test_old_monolithic_main_tf_no_longer_exists(self):
        self.assertFalse(
            os.path.isfile(OLD_MONOLITHIC_MAIN_TF),
            "terraform/modules/asg/main.tf should have been removed by the split "
            "into asg.tf/data.tf/iam.tf/launch_template.tf/scaling_policies.tf",
        )

    def test_every_expected_block_present_exactly_once_in_its_own_file(self):
        for block, file_key in EXPECTED_BLOCK_LOCATIONS.items():
            with self.subTest(block=block):
                self.assertEqual(
                    self.contents[file_key].count(block),
                    1,
                    f"Expected exactly one occurrence of {block!r} in "
                    f"{SPLIT_FILES[file_key]}",
                )

    def test_blocks_not_leaked_into_other_files(self):
        for block, owning_key in EXPECTED_BLOCK_LOCATIONS.items():
            for name, content in self.contents.items():
                if name == owning_key:
                    continue
                with self.subTest(block=block, file=name):
                    self.assertNotIn(
                        block,
                        content,
                        f"{block!r} should only be declared in "
                        f"{SPLIT_FILES[owning_key]}, not also in {SPLIT_FILES[name]}",
                    )

    def test_no_resource_or_data_block_is_duplicated_across_the_module(self):
        combined = "\n".join(self.contents.values())
        for block in EXPECTED_BLOCK_LOCATIONS:
            with self.subTest(block=block):
                self.assertEqual(combined.count(block), 1)

    def test_module_still_defines_the_same_resource_and_data_block_count(self):
        """Regression: the split must not silently drop or duplicate any
        resource/data block relative to the pre-split main.tf, which
        declared exactly these 11 blocks."""
        combined = "\n".join(self.contents.values())
        total = sum(combined.count(block) for block in EXPECTED_BLOCK_LOCATIONS)
        self.assertEqual(total, len(EXPECTED_BLOCK_LOCATIONS))


class AsgModuleCrossFileReferenceTestCase(unittest.TestCase):
    """Confirms the cross-file references between the split files survived
    the refactor (e.g. the launch template still points at the IAM
    instance profile and the AMI-selection locals; the ASG still points at
    the launch template; the scaling policies/alarms still point at the
    ASG)."""

    @classmethod
    def setUpClass(cls):
        cls.contents = {name: _read(path) for name, path in SPLIT_FILES.items()}

    def test_launch_template_references_selected_ami_local_from_data_tf(self):
        self.assertIn("local.selected_ami_id", self.contents["launch_template"])

    def test_launch_template_references_instance_profile_arn_from_iam_tf(self):
        self.assertIn(
            "aws_iam_instance_profile.instance_profile.arn",
            self.contents["launch_template"],
        )

    def test_asg_references_launch_template_id(self):
        self.assertIn("aws_launch_template.main.id", self.contents["asg"])

    def test_scaling_policies_and_alarms_reference_asg_name_four_times(self):
        # 2 aws_autoscaling_policy blocks + 2 aws_cloudwatch_metric_alarm
        # dimensions blocks, each referencing aws_autoscaling_group.main.name.
        self.assertEqual(
            self.contents["scaling_policies"].count(
                "aws_autoscaling_group.main.name"
            ),
            4,
        )

    def test_alarms_reference_their_respective_scaling_policy_arns(self):
        self.assertIn(
            "alarm_actions = [aws_autoscaling_policy.scale_out.arn]",
            self.contents["scaling_policies"],
        )
        self.assertIn(
            "alarm_actions = [aws_autoscaling_policy.scale_in.arn]",
            self.contents["scaling_policies"],
        )

    def test_iam_instance_profile_references_iam_role(self):
        block = _extract_top_level_block(
            self.contents["iam"], 'resource "aws_iam_instance_profile" "instance_profile" {'
        )
        self.assertRegex(block, r"role\s*=\s*aws_iam_role\.instance_role\.name")

    def test_iam_role_policy_attachment_references_iam_role(self):
        block = _extract_top_level_block(
            self.contents["iam"],
            'resource "aws_iam_role_policy_attachment" "ssm_policy" {',
        )
        self.assertRegex(block, r"role\s*=\s*aws_iam_role\.instance_role\.name")

    def test_data_tf_ami_selection_locals_chain_together(self):
        content = self.contents["data"]
        # `selected_ami_id` is declared (not self-referenced) in data.tf;
        # `is_arm64` and `default_ami_id` are each referenced (via the
        # `local.` prefix) by the *next* local in the chain.
        self.assertIn("selected_ami_id", content)
        self.assertIn("local.is_arm64", content)
        self.assertIn("local.default_ami_id", content)
        self.assertIn("data.aws_ssm_parameter.al2023_arm64.value", content)
        self.assertIn("data.aws_ssm_parameter.al2023_x86_64.value", content)
        self.assertIn("var.ami_id", content)


class AsgModuleIamConfigurationTestCase(unittest.TestCase):
    """Focused checks on the IAM configuration extracted into iam.tf."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(IAM_TF)

    def test_assume_role_policy_trusts_ec2_service(self):
        collapsed = "".join(self.content.split())
        self.assertIn('Action="sts:AssumeRole"', collapsed)
        self.assertIn('Effect="Allow"', collapsed)
        self.assertIn('Service="ec2.amazonaws.com"', collapsed)

    def test_ssm_managed_instance_core_policy_attached(self):
        self.assertRegex(
            self.content,
            r'policy_arn\s*=\s*"arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"',
        )

    def test_role_and_profile_names_are_environment_scoped(self):
        self.assertRegex(
            self.content,
            r'name\s*=\s*"\$\{var\.environment\}-asg-instance-role"',
        )
        self.assertRegex(
            self.content,
            r'name\s*=\s*"\$\{var\.environment\}-asg-instance-profile"',
        )


class AsgModuleScalingPolicyConfigurationTestCase(unittest.TestCase):
    """Focused checks on the scaling policies/alarms extracted into
    scaling_policies.tf."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SCALING_POLICIES_TF)

    def test_scale_out_policy_increments_capacity_by_one(self):
        block = _extract_top_level_block(
            self.content, 'resource "aws_autoscaling_policy" "scale_out" {'
        )
        self.assertRegex(block, r"scaling_adjustment\s*=\s*1\b")

    def test_scale_in_policy_decrements_capacity_by_one(self):
        block = _extract_top_level_block(
            self.content, 'resource "aws_autoscaling_policy" "scale_in" {'
        )
        self.assertRegex(block, r"scaling_adjustment\s*=\s*-1\b")

    def test_both_policies_use_change_in_capacity_adjustment_type(self):
        self.assertEqual(
            len(re.findall(r'adjustment_type\s*=\s*"ChangeInCapacity"', self.content)),
            2,
        )

    def test_both_policies_share_the_same_cooldown(self):
        self.assertEqual(len(re.findall(r"cooldown\s*=\s*300\b", self.content)), 2)

    def test_high_cpu_alarm_thresholds(self):
        block = _extract_top_level_block(
            self.content, 'resource "aws_cloudwatch_metric_alarm" "cpu_high" {'
        )
        self.assertRegex(
            block, r'comparison_operator\s*=\s*"GreaterThanOrEqualToThreshold"'
        )
        self.assertRegex(block, r"threshold\s*=\s*70\b")

    def test_low_cpu_alarm_thresholds(self):
        block = _extract_top_level_block(
            self.content, 'resource "aws_cloudwatch_metric_alarm" "cpu_low" {'
        )
        self.assertRegex(
            block, r'comparison_operator\s*=\s*"LessThanOrEqualToThreshold"'
        )
        self.assertRegex(block, r"threshold\s*=\s*30\b")

    def test_alarms_use_ec2_cpu_utilization_metric(self):
        self.assertEqual(
            len(re.findall(r'metric_name\s*=\s*"CPUUtilization"', self.content)), 2
        )
        self.assertEqual(
            len(re.findall(r'namespace\s*=\s*"AWS/EC2"', self.content)), 2
        )

    def test_alarm_evaluation_periods_are_two_for_both_alarms(self):
        self.assertEqual(
            len(re.findall(r"evaluation_periods\s*=\s*2\b", self.content)), 2
        )


class AsgModuleAutoScalingGroupConfigurationTestCase(unittest.TestCase):
    """Focused checks on the Auto Scaling Group resource extracted into
    asg.tf."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASG_TF)

    def test_uses_elb_health_checks_with_grace_period(self):
        self.assertRegex(self.content, r'health_check_type\s*=\s*"ELB"')
        self.assertRegex(self.content, r"health_check_grace_period\s*=\s*300\b")

    def test_sizing_driven_by_variables(self):
        self.assertRegex(self.content, r"min_size\s*=\s*var\.min_size")
        self.assertRegex(self.content, r"max_size\s*=\s*var\.max_size")
        self.assertRegex(
            self.content, r"desired_capacity\s*=\s*var\.desired_capacity"
        )

    def test_uses_latest_launch_template_version(self):
        self.assertRegex(
            self.content,
            r'version\s*=\s*(?:"\$Latest"|aws_launch_template\.main\.latest_version)',
        )

    def test_rolling_instance_refresh_with_fifty_percent_min_healthy(self):
        self.assertRegex(self.content, r'strategy\s*=\s*"Rolling"')
        self.assertRegex(self.content, r"min_healthy_percentage\s*=\s*50\b")
        self.assertRegex(self.content, r'triggers\s*=\s*\["tag"\]')

    def test_desired_capacity_ignored_on_subsequent_applies(self):
        # Regression: without this, externally-driven autoscaling activity
        # (e.g. from the CPU-based scaling policies) would be reverted on
        # every subsequent `apply`.
        self.assertRegex(
            self.content, r"ignore_changes\s*=\s*\[desired_capacity\]"
        )

    def test_environment_tag_propagates_to_instances(self):
        self.assertRegex(self.content, r'key\s*=\s*"Environment"')
        self.assertRegex(self.content, r"propagate_at_launch\s*=\s*true")

    def test_force_delete_and_create_before_destroy_are_enabled(self):
        self.assertRegex(self.content, r"force_delete\s*=\s*true")
        self.assertRegex(self.content, r"create_before_destroy\s*=\s*true")


if __name__ == "__main__":
    unittest.main()