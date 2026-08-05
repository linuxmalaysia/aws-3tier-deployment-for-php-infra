"""
Unit tests for terraform/variables.tf and terraform/terraform.tfvars.example

This PR updated variable descriptions to reference "developer server
specifications" (instead of "developer specifications") and refreshed the
instance-type guidance comments in the example tfvars file to reflect the
Nginx + PHP-FPM CodeIgniter architecture instead of the retired
Server01/02/03 AI-tier naming scheme.
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VARIABLES_PATH = os.path.join(REPO_ROOT, "terraform", "variables.tf")
TFVARS_EXAMPLE_PATH = os.path.join(REPO_ROOT, "terraform", "terraform.tfvars.example")

VARIABLE_BLOCK_RE = re.compile(
    r'variable\s+"([a-zA-Z0-9_]+)"\s*\{(.*?)\n\}', re.DOTALL
)
DEFAULT_RE = re.compile(r'default\s*=\s*(.+)')
TYPE_RE = re.compile(r'type\s*=\s*(.+)')
SENSITIVE_RE = re.compile(r'sensitive\s*=\s*(true|false)')


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_variables(content):
    """Return a dict of variable name -> block body text."""
    return {name: body for name, body in VARIABLE_BLOCK_RE.findall(content)}


def _parse_tfvars_assignments(content):
    """Return a dict of assigned variable name -> raw RHS text (single line)."""
    assignments = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r'^([a-zA-Z0-9_]+)\s*=\s*(.+)$', stripped)
        if match:
            assignments[match.group(1)] = match.group(2)
    return assignments


class TerraformFilesExistTest(unittest.TestCase):
    def test_variables_tf_exists(self):
        self.assertTrue(os.path.isfile(VARIABLES_PATH))

    def test_tfvars_example_exists(self):
        self.assertTrue(os.path.isfile(TFVARS_EXAMPLE_PATH))


class VariablesDescriptionRegressionTest(unittest.TestCase):
    """Regression tests for this PR's description wording changes."""

    def setUp(self):
        self.variables = _parse_variables(_load(VARIABLES_PATH))

    def test_db_instance_class_description_mentions_developer_server_specs(self):
        self.assertIn("db_instance_class", self.variables)
        self.assertIn("developer server specifications", self.variables["db_instance_class"])

    def test_instance_type_description_mentions_developer_server_specs(self):
        self.assertIn("instance_type", self.variables)
        self.assertIn("developer server specifications", self.variables["instance_type"])

    def test_no_leftover_ambiguous_developer_specifications_wording(self):
        # Ensure the old, less precise wording was fully replaced (not just
        # partially duplicated) in the two updated variable blocks.
        for name in ("db_instance_class", "instance_type"):
            body = self.variables[name]
            self.assertNotRegex(
                body,
                r"developer specifications(?!\s)",
                f"{name} still contains old ambiguous wording",
            )


class VariablesStructureTest(unittest.TestCase):
    def setUp(self):
        self.variables = _parse_variables(_load(VARIABLES_PATH))

    def test_expected_core_variables_declared(self):
        expected = [
            "aws_region", "environment", "vpc_cidr", "instance_type",
            "ami_id", "min_size", "max_size", "desired_capacity",
            "db_engine", "db_engine_version", "db_instance_class",
            "db_name", "db_username", "db_password", "http_port", "db_port",
            "enable_standalone_ec2", "standalone_ec2_instance_type",
            "standalone_ec2_count", "standalone_ec2_ami_id",
            "standalone_ubuntu_ami_filter_name",
            "enable_elasticache_valkey", "valkey_node_type",
            "enable_jumphost", "jumphost_instance_type",
        ]
        for var_name in expected:
            self.assertIn(var_name, self.variables, f"missing expected variable: {var_name}")

    def test_aws_region_defaults_to_malaysia(self):
        body = self.variables["aws_region"]
        default_match = DEFAULT_RE.search(body)
        self.assertIsNotNone(default_match)
        self.assertEqual(default_match.group(1).strip(), '"ap-southeast-5"')

    def test_db_password_is_sensitive_and_has_no_default(self):
        body = self.variables["db_password"]
        sensitive_match = SENSITIVE_RE.search(body)
        self.assertIsNotNone(sensitive_match)
        self.assertEqual(sensitive_match.group(1), "true")
        self.assertIsNone(DEFAULT_RE.search(body), "db_password must not have a default value")

    def test_http_and_db_port_defaults(self):
        http_default = DEFAULT_RE.search(self.variables["http_port"]).group(1).strip()
        db_default = DEFAULT_RE.search(self.variables["db_port"]).group(1).strip()
        self.assertEqual(http_default, "80")
        self.assertEqual(db_default, "5432")

    def test_asg_sizing_defaults_are_consistent(self):
        min_size = int(DEFAULT_RE.search(self.variables["min_size"]).group(1).strip())
        max_size = int(DEFAULT_RE.search(self.variables["max_size"]).group(1).strip())
        desired = int(DEFAULT_RE.search(self.variables["desired_capacity"]).group(1).strip())
        self.assertLessEqual(min_size, desired)
        self.assertLessEqual(desired, max_size)


class TfvarsExampleConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.variables = _parse_variables(_load(VARIABLES_PATH))
        self.assignments = _parse_tfvars_assignments(_load(TFVARS_EXAMPLE_PATH))
        self.tfvars_content = _load(TFVARS_EXAMPLE_PATH)

    def test_every_assignment_maps_to_a_declared_variable(self):
        unknown = [name for name in self.assignments if name not in self.variables]
        self.assertEqual(unknown, [], f"tfvars.example assigns undeclared variables: {unknown}")

    def test_db_password_placeholder_present_and_flagged_for_change(self):
        self.assertIn("db_password", self.assignments)
        self.assertIn("YOUR_SECURE_PASSWORD_HERE", self.assignments["db_password"])
        # The line should carry a comment reminding operators to change it.
        line = next(l for l in self.tfvars_content.splitlines() if l.strip().startswith("db_password"))
        self.assertIn("# Change this!", line)

    def test_instance_type_comment_reflects_nginx_and_php_fpm_architecture(self):
        self.assertIn("Matches Nginx frontend", self.tfvars_content)
        self.assertIn("Matches heavy PHP-FPM processing", self.tfvars_content)

    def test_instance_type_comment_no_longer_references_retired_server_ai_tier_naming(self):
        self.assertNotIn("Matches Server 01 Frontend", self.tfvars_content)
        self.assertNotIn("Server 03 AI workloads", self.tfvars_content)

    def test_region_and_environment_assignments_match_variable_defaults(self):
        self.assertEqual(self.assignments["aws_region"], '"ap-southeast-5"')
        self.assertEqual(self.assignments["environment"], '"production"')


if __name__ == "__main__":
    unittest.main()