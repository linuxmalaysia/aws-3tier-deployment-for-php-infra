#!/usr/bin/env python3
"""Unit/functional tests for the parallelized IMDSv2 metadata retrieval logic
embedded in the ``user_data`` heredocs of the Terraform/OpenTofu EC2 modules:

* ``terraform/modules/asg/main.tf``            -- ``aws_launch_template.main``
* ``terraform/modules/standalone_ec2/main.tf``  -- ``aws_instance.standalone``

Both modules embed a copy of the same bash bootstrap logic found in
``scripts/user_data.sh`` (see
``tests/test_user_data_metadata_retrieval.py``): the two previously
sequential, blocking ``curl`` calls for ``instance-id`` and
``placement/availability-zone`` are now backgrounded, their PIDs captured,
waited on together, read back from temp files, given an explicit
empty-value fallback, and the temp files cleaned up.

These ``.tf`` files are treated as plain text (regex-based structural
checks), following the dependency-free convention already used throughout
this repository's test suite (e.g. ``tests/test_security_posture_assessment_docs.py``).
In addition, the embedded bash snippet is extracted and actually executed
under ``bash`` with a stubbed ``curl`` on ``PATH`` to verify runtime
behavior -- since Terraform's ``<<-EOF`` heredoc only strips leading tabs
(not the spaces used here) and neither module uses ``${...}`` interpolation
on the metadata variables, the extracted snippet is valid, self-contained
bash that runs identically to the standalone script. No real network access
is performed.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_terraform_ec2_metadata_retrieval
"""
import os
import re
import stat
import subprocess
import tempfile
import time
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "user_data.sh")
ASG_MAIN_TF = os.path.join(REPO_ROOT, "terraform", "modules", "asg", "main.tf")
STANDALONE_MAIN_TF = os.path.join(
    REPO_ROOT, "terraform", "modules", "standalone_ec2", "main.tf"
)

TOKEN_START_MARKER = (
    'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token"'
)

TMP_INSTANCE_ID_FILE = "/tmp/instance_id"
TMP_AZ_FILE = "/tmp/az"

FAKE_CURL_SCRIPT = r"""#!/bin/bash
# Fake curl stub used by tests: never touches the network.
args="$*"

if [[ "$args" == *"/latest/api/token"* ]]; then
    if [[ -n "${FAKE_CURL_TOKEN_DELAY:-}" ]]; then
        sleep "${FAKE_CURL_TOKEN_DELAY}"
    fi
    if [[ -n "${FAKE_CURL_TOKEN_FAIL:-}" ]]; then
        exit 1
    fi
    printf '%s' "${FAKE_CURL_TOKEN:-FAKETOKEN123}"
    exit 0
fi

if [[ "$args" == *"meta-data/instance-id"* ]]; then
    if [[ -n "${FAKE_CURL_INSTANCE_DELAY:-}" ]]; then
        sleep "${FAKE_CURL_INSTANCE_DELAY}"
    fi
    if [[ -n "${FAKE_CURL_INSTANCE_FAIL:-}" ]]; then
        exit 1
    fi
    printf '%s' "${FAKE_CURL_INSTANCE_ID:-i-0123456789abcdef0}"
    exit 0
fi

if [[ "$args" == *"placement/availability-zone"* ]]; then
    if [[ -n "${FAKE_CURL_AZ_DELAY:-}" ]]; then
        sleep "${FAKE_CURL_AZ_DELAY}"
    fi
    if [[ -n "${FAKE_CURL_AZ_FAIL:-}" ]]; then
        exit 1
    fi
    printf '%s' "${FAKE_CURL_AZ:-ap-southeast-5a}"
    exit 0
fi

exit 1
"""


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_metadata_block(content, start_marker=TOKEN_START_MARKER):
    """Extract the self-contained ``TOKEN=... ; if ... fi`` metadata
    retrieval block from a bootstrap script's (or Terraform heredoc's)
    source text."""
    start = content.index(start_marker)
    fi_match = re.search(r"\n[ \t]*fi\b", content[start:])
    assert fi_match is not None, "Could not locate closing 'fi' for metadata block"
    end = start + fi_match.end()
    return content[start:end]


def _normalize(block):
    """Normalize a block for cross-file structural comparison by stripping
    each line's surrounding (indentation) whitespace and dropping blank
    lines. This lets us compare the logically-identical metadata blocks
    embedded at different indentation depths (and with cosmetic blank-line
    differences) in scripts/user_data.sh vs. the two Terraform heredocs."""
    lines = [line.strip() for line in block.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def _make_executable(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


class TerraformUserDataStructureTestCase(unittest.TestCase):
    """Structural/regex-based checks shared by both Terraform modules'
    embedded metadata-retrieval blocks."""

    MODULE_PATHS = {
        "asg": ASG_MAIN_TF,
        "standalone_ec2": STANDALONE_MAIN_TF,
    }

    @classmethod
    def setUpClass(cls):
        cls.contents = {name: _read(path) for name, path in cls.MODULE_PATHS.items()}
        cls.blocks = {
            name: _extract_metadata_block(content)
            for name, content in cls.contents.items()
        }

    def test_module_files_exist(self):
        for name, path in self.MODULE_PATHS.items():
            with self.subTest(module=name):
                self.assertTrue(os.path.isfile(path))

    def test_token_retrieval_line_present(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn(
                    'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" '
                    '-H "X-aws-ec2-metadata-token-ttl-seconds: 21600" --max-time 2 '
                    '--connect-timeout 2 || echo "")',
                    content,
                )

    def test_instance_id_curl_is_backgrounded_and_redirected(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn(
                    'curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
                    "http://169.254.169.254/latest/meta-data/instance-id "
                    "--max-time 2 --connect-timeout 2 > /tmp/instance_id "
                    "2>/dev/null &",
                    content,
                )

    def test_az_curl_is_backgrounded_and_redirected(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn(
                    'curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
                    "http://169.254.169.254/latest/meta-data/placement/"
                    "availability-zone --max-time 2 --connect-timeout 2 "
                    "> /tmp/az 2>/dev/null &",
                    content,
                )

    def test_pids_captured_for_both_background_jobs(self):
        for name, block in self.blocks.items():
            with self.subTest(module=name):
                self.assertIn("PID_ID=$!", block)
                self.assertIn("PID_AZ=$!", block)

    def test_waits_on_both_pids_with_guard(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn("wait $PID_ID $PID_AZ || true", content)

    def test_explicit_empty_value_fallback_present(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn(
                    '[ -z "$INSTANCE_ID" ] && INSTANCE_ID="unknown-instance-id"',
                    content,
                )
                self.assertIn('[ -z "$AZ" ] && AZ="unknown-az"', content)

    def test_temp_files_cleaned_up(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertIn("rm -f /tmp/instance_id /tmp/az", content)

    def test_else_branch_for_missing_token_unchanged(self):
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertRegex(
                    content,
                    re.compile(
                        r'else\n\s*INSTANCE_ID="unknown-instance-id"\n\s*'
                        r'AZ="unknown-az"\n\s*fi',
                    ),
                )

    def test_old_sequential_curl_assignment_pattern_absent(self):
        """Regression: the previous non-parallel implementation directly
        assigned INSTANCE_ID/AZ from a single blocking curl call each."""
        for name, content in self.contents.items():
            with self.subTest(module=name):
                self.assertNotIn(
                    'INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
                    "http://169.254.169.254/latest/meta-data/instance-id",
                    content,
                )
                self.assertNotIn(
                    'AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
                    "http://169.254.169.254/latest/meta-data/placement/"
                    "availability-zone",
                    content,
                )

    def test_asg_metadata_block_embedded_inside_base64encode_user_data(self):
        content = self.contents["asg"]
        user_data_idx = content.index("user_data = base64encode(<<-EOF")
        token_idx = content.index(TOKEN_START_MARKER)
        eof_idx = content.rindex("\n  )", token_idx)
        self.assertLess(user_data_idx, token_idx)
        self.assertLess(token_idx, eof_idx)

    def test_standalone_metadata_block_embedded_inside_plain_heredoc_user_data(self):
        content = self.contents["standalone_ec2"]
        user_data_idx = content.index("user_data = <<-EOF")
        token_idx = content.index(TOKEN_START_MARKER)
        self.assertLess(user_data_idx, token_idx)
        # Unlike the ASG module, standalone_ec2's user_data is a plain
        # heredoc string (not wrapped in base64encode()).
        user_data_line = content.splitlines()[
            content[:user_data_idx].count("\n")
        ]
        self.assertNotIn("base64encode", user_data_line)


class TerraformUserDataCrossFileConsistencyTestCase(unittest.TestCase):
    """Verifies the metadata retrieval block is textually identical (modulo
    indentation) across scripts/user_data.sh and both Terraform modules,
    guarding against silent drift between the three copies."""

    @classmethod
    def setUpClass(cls):
        cls.script_block = _normalize(
            _extract_metadata_block(_read(SCRIPT_PATH))
        )
        cls.asg_block = _normalize(
            _extract_metadata_block(_read(ASG_MAIN_TF))
        )
        cls.standalone_block = _normalize(
            _extract_metadata_block(_read(STANDALONE_MAIN_TF))
        )

    def test_asg_block_matches_standalone_script_block(self):
        self.assertEqual(self.asg_block, self.script_block)

    def test_standalone_ec2_block_matches_standalone_script_block(self):
        self.assertEqual(self.standalone_block, self.script_block)

    def test_asg_block_matches_standalone_ec2_block(self):
        self.assertEqual(self.asg_block, self.standalone_block)


class TerraformUserDataMetadataFunctionalTestCase(unittest.TestCase):
    """Executes the metadata-retrieval bash logic extracted from each
    Terraform module's embedded heredoc against a stubbed curl, to verify
    runtime behavior identical to scripts/user_data.sh."""

    MODULE_PATHS = {
        "asg": ASG_MAIN_TF,
        "standalone_ec2": STANDALONE_MAIN_TF,
    }

    @classmethod
    def setUpClass(cls):
        cls.blocks = {
            name: _extract_metadata_block(_read(path))
            for name, path in cls.MODULE_PATHS.items()
        }

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        fake_curl_path = os.path.join(self._tmpdir.name, "curl")
        _make_executable(fake_curl_path, FAKE_CURL_SCRIPT)

        self._env = dict(os.environ)
        self._env["PATH"] = self._tmpdir.name + os.pathsep + self._env.get("PATH", "")
        for path in (TMP_INSTANCE_ID_FILE, TMP_AZ_FILE):
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        self._tmpdir.cleanup()
        for path in (TMP_INSTANCE_ID_FILE, TMP_AZ_FILE):
            if os.path.exists(path):
                os.remove(path)

    def _run_block(self, module, extra_env=None, timeout=10):
        wrapper = (
            "#!/bin/bash\n"
            "set -euo pipefail\n"
            + self.blocks[module]
            + "\n"
            'printf "RESULT_INSTANCE_ID=%s\\nRESULT_AZ=%s\\n" "$INSTANCE_ID" "$AZ"\n'
        )
        script_path = os.path.join(self._tmpdir.name, "run_block.sh")
        _make_executable(script_path, wrapper)

        env = dict(self._env)
        if extra_env:
            env.update(extra_env)

        start = time.monotonic()
        proc = subprocess.run(
            ["bash", script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        return proc, elapsed

    @staticmethod
    def _parse_results(stdout):
        instance_match = re.search(r"^RESULT_INSTANCE_ID=(.*)$", stdout, re.MULTILINE)
        az_match = re.search(r"^RESULT_AZ=(.*)$", stdout, re.MULTILINE)
        return (
            instance_match.group(1) if instance_match else None,
            az_match.group(1) if az_match else None,
        )

    def test_successful_retrieval_for_each_module(self):
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, _ = self._run_block(
                    module,
                    {
                        "FAKE_CURL_INSTANCE_ID": "i-tf-%s" % module,
                        "FAKE_CURL_AZ": "ap-southeast-5b",
                    },
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                instance_id, az = self._parse_results(proc.stdout)
                self.assertEqual(instance_id, "i-tf-%s" % module)
                self.assertEqual(az, "ap-southeast-5b")

    def test_temp_files_removed_after_run_for_each_module(self):
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, _ = self._run_block(module)
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                self.assertFalse(os.path.exists(TMP_INSTANCE_ID_FILE))
                self.assertFalse(os.path.exists(TMP_AZ_FILE))

    def test_parallel_execution_is_faster_than_sequential_for_each_module(self):
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, elapsed = self._run_block(
                    module,
                    {
                        "FAKE_CURL_INSTANCE_DELAY": "0.4",
                        "FAKE_CURL_AZ_DELAY": "0.4",
                    },
                    timeout=15,
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                self.assertLess(
                    elapsed,
                    0.75,
                    msg=(
                        "Module '%s' metadata retrieval took %.2fs; expected "
                        "concurrent (~0.4s) rather than sequential (~0.8s) "
                        "execution" % (module, elapsed)
                    ),
                )

    def test_missing_token_falls_back_to_unknown_for_each_module(self):
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, _ = self._run_block(module, {"FAKE_CURL_TOKEN_FAIL": "1"})
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                instance_id, az = self._parse_results(proc.stdout)
                self.assertEqual(instance_id, "unknown-instance-id")
                self.assertEqual(az, "unknown-az")

    def test_partial_failure_falls_back_only_for_the_failed_value(self):
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, _ = self._run_block(
                    module,
                    {
                        "FAKE_CURL_AZ_FAIL": "1",
                        "FAKE_CURL_INSTANCE_ID": "i-partial-ok",
                    },
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                instance_id, az = self._parse_results(proc.stdout)
                self.assertEqual(instance_id, "i-partial-ok")
                self.assertEqual(az, "unknown-az")

    def test_both_fetches_fail_but_script_still_completes_for_each_module(self):
        """Regression: 'wait $PID_ID $PID_AZ || true' must prevent 'set -e'
        from aborting the script even when both background curls fail."""
        for module in self.MODULE_PATHS:
            with self.subTest(module=module):
                proc, _ = self._run_block(
                    module,
                    {
                        "FAKE_CURL_INSTANCE_FAIL": "1",
                        "FAKE_CURL_AZ_FAIL": "1",
                    },
                )
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                instance_id, az = self._parse_results(proc.stdout)
                self.assertEqual(instance_id, "unknown-instance-id")
                self.assertEqual(az, "unknown-az")
                self.assertFalse(os.path.exists(TMP_INSTANCE_ID_FILE))
                self.assertFalse(os.path.exists(TMP_AZ_FILE))


if __name__ == "__main__":
    unittest.main()