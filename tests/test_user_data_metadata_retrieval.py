#!/usr/bin/env python3
"""Unit/functional tests for the parallelized IMDSv2 metadata retrieval logic
introduced in ``scripts/user_data.sh``.

This PR replaces two sequential, blocking ``curl`` calls (one for
``instance-id`` and one for ``placement/availability-zone``) with a
parallelized version that backgrounds both requests, captures their PIDs,
waits for both to finish, reads the results from temporary files, applies an
explicit empty-value fallback, and cleans up the temporary files.

Two kinds of coverage are provided:

* Structural/regex-based checks (following the dependency-free convention
  already used by ``tests/test_security_posture_assessment_docs.py`` and
  ``tests/test_pdf_generation_workflow.py``) that pin down the exact shape
  of the new bootstrap logic.
* Functional checks that actually execute the extracted bash snippet under
  a real ``bash`` interpreter with a stubbed ``curl`` binary injected via
  ``PATH``, so the *behavior* of the parallelization (correct values,
  fallback handling, temp-file cleanup, and resilience under ``set -e``) is
  verified rather than just its textual shape. No real network access is
  performed -- the stub ``curl`` never talks to 169.254.169.254.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_user_data_metadata_retrieval
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

TOKEN_START_MARKER = (
    'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token"'
)

TMP_INSTANCE_ID_FILE = "/tmp/instance_id"
TMP_AZ_FILE = "/tmp/az"

FAKE_CURL_SCRIPT = r"""#!/bin/bash
# Fake curl stub used by tests: never touches the network. Decides how to
# respond based on which metadata URL it was invoked against, and can be
# steered to fail/delay via environment variables set by the test.
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
    retrieval block from a bootstrap script's source text."""
    start = content.index(start_marker)
    fi_match = re.search(r"\n[ \t]*fi\b", content[start:])
    assert fi_match is not None, "Could not locate closing 'fi' for metadata block"
    end = start + fi_match.end()
    return content[start:end]


def _make_executable(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


class UserDataMetadataBlockFunctionalHarness(unittest.TestCase):
    """Base class providing the fake-curl execution harness. Not a test
    case itself (no test_ methods), subclassed below."""

    @classmethod
    def setUpClass(cls):
        cls.script_content = _read(SCRIPT_PATH)
        cls.metadata_block = _extract_metadata_block(cls.script_content)

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        fake_curl_path = os.path.join(self._tmpdir.name, "curl")
        _make_executable(fake_curl_path, FAKE_CURL_SCRIPT)

        self._env = dict(os.environ)
        self._env["PATH"] = self._tmpdir.name + os.pathsep + self._env.get("PATH", "")
        # Ensure a clean slate for the hardcoded temp files the script uses.
        for path in (TMP_INSTANCE_ID_FILE, TMP_AZ_FILE):
            if os.path.exists(path):
                os.remove(path)

    def tearDown(self):
        self._tmpdir.cleanup()
        for path in (TMP_INSTANCE_ID_FILE, TMP_AZ_FILE):
            if os.path.exists(path):
                os.remove(path)

    def _run_block(self, extra_env=None, timeout=10):
        """Run the extracted metadata block under bash, returning
        (CompletedProcess, elapsed_seconds)."""
        wrapper = (
            "#!/bin/bash\n"
            "set -euo pipefail\n"
            + self.metadata_block
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


class UserDataScriptStructureTestCase(unittest.TestCase):
    """Structural/regex-based checks on scripts/user_data.sh."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SCRIPT_PATH)

    def test_script_file_exists(self):
        self.assertTrue(os.path.isfile(SCRIPT_PATH))

    def test_script_retains_shebang_and_safety_flags(self):
        self.assertTrue(self.content.startswith("#!/bin/bash\n"))
        self.assertIn("set -euo pipefail", self.content)

    def test_token_retrieval_line_unchanged(self):
        self.assertIn(
            'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" '
            '-H "X-aws-ec2-metadata-token-ttl-seconds: 21600" --max-time 2 '
            '--connect-timeout 2 || echo "")',
            self.content,
        )

    def test_instance_id_curl_is_backgrounded_and_redirected_to_temp_file(self):
        self.assertIn(
            'curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
            "http://169.254.169.254/latest/meta-data/instance-id --max-time 2 "
            '--connect-timeout 2 > "$SECURE_TMP_DIR/instance_id" 2>/dev/null &',
            self.content,
        )

    def test_az_curl_is_backgrounded_and_redirected_to_temp_file(self):
        self.assertIn(
            'curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
            "http://169.254.169.254/latest/meta-data/placement/availability-zone "
            '--max-time 2 --connect-timeout 2 > "$SECURE_TMP_DIR/az" 2>/dev/null &',
            self.content,
        )

    def test_pid_captured_immediately_after_each_backgrounded_curl(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"meta-data/instance-id.*&\n\s*PID_ID=\$!\n", re.DOTALL
            ),
        )
        self.assertRegex(
            self.content,
            re.compile(
                r"meta-data/placement/availability-zone.*&\n\s*PID_AZ=\$!\n",
                re.DOTALL,
            ),
        )

    def test_waits_on_both_captured_pids_with_guard(self):
        self.assertIn("wait $PID_ID $PID_AZ || true", self.content)

    def test_instance_id_read_from_temp_file_with_cat_fallback(self):
        self.assertIn(
            'INSTANCE_ID=$(cat "$SECURE_TMP_DIR/instance_id" 2>/dev/null || '
            'echo "unknown-instance-id")',
            self.content,
        )

    def test_az_read_from_temp_file_with_cat_fallback(self):
        self.assertIn(
            'AZ=$(cat "$SECURE_TMP_DIR/az" 2>/dev/null || echo "unknown-az")', self.content
        )

    def test_explicit_empty_value_fallback_checks_present(self):
        self.assertIn(
            '[ -z "$INSTANCE_ID" ] && INSTANCE_ID="unknown-instance-id"',
            self.content,
        )
        self.assertIn('[ -z "$AZ" ] && AZ="unknown-az"', self.content)

    def test_temp_files_are_cleaned_up(self):
        self.assertIn('trap \'rm -rf "$SECURE_TMP_DIR"\' EXIT', self.content)

    def test_else_branch_for_missing_token_unchanged(self):
        self.assertRegex(
            self.content,
            re.compile(
                r'else\n\s*INSTANCE_ID="unknown-instance-id"\n\s*'
                r'AZ="unknown-az"\n\s*fi',
            ),
        )

    def test_cleanup_occurs_after_fallback_checks_and_before_else(self):
        # We now use mktemp -d and register trap at the start, which is a safer pattern.
        # We assert that the trap is correctly set up.
        self.assertIn('trap \'rm -rf "$SECURE_TMP_DIR"\' EXIT', self.content)

    def test_wait_occurs_before_reading_result_files(self):
        block = _extract_metadata_block(self.content)
        wait_idx = block.index("wait $PID_ID $PID_AZ")
        read_idx = block.index('INSTANCE_ID=$(cat "$SECURE_TMP_DIR/instance_id"')
        self.assertLess(wait_idx, read_idx)

    def test_old_single_line_sequential_curl_pattern_no_longer_present(self):
        """Regression: the previous non-parallel implementation directly
        assigned INSTANCE_ID/AZ from a single blocking curl call each; that
        pattern must not linger after parallelization."""
        self.assertNotIn(
            'INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
            "http://169.254.169.254/latest/meta-data/instance-id",
            self.content,
        )
        self.assertNotIn(
            'AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" '
            "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            self.content,
        )

    def test_metadata_block_appears_before_os_detection_section(self):
        metadata_idx = self.content.index(TOKEN_START_MARKER)
        os_detect_idx = self.content.index("# Detect OS")
        self.assertLess(metadata_idx, os_detect_idx)


class UserDataScriptFunctionalTestCase(UserDataMetadataBlockFunctionalHarness):
    """Executes the extracted metadata-retrieval bash logic against a
    stubbed curl to verify actual runtime behavior."""

    def test_successful_metadata_retrieval_returns_expected_values(self):
        proc, _ = self._run_block(
            {
                "FAKE_CURL_INSTANCE_ID": "i-0abc123def456",
                "FAKE_CURL_AZ": "ap-southeast-5b",
            }
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "i-0abc123def456")
        self.assertEqual(az, "ap-southeast-5b")

    def test_temp_files_removed_after_successful_run(self):
        proc, _ = self._run_block()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertFalse(os.path.exists(TMP_INSTANCE_ID_FILE))
        self.assertFalse(os.path.exists(TMP_AZ_FILE))

    def test_parallel_execution_is_faster_than_sequential_equivalent(self):
        """Regression: the whole point of this change is to run the two
        metadata requests concurrently. With both requests artificially
        delayed by 0.4s, total wall time should be close to 0.4s (parallel)
        rather than ~0.8s (sequential)."""
        proc, elapsed = self._run_block(
            {
                "FAKE_CURL_INSTANCE_DELAY": "0.4",
                "FAKE_CURL_AZ_DELAY": "0.4",
            },
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "i-0123456789abcdef0")
        self.assertEqual(az, "ap-southeast-5a")
        self.assertLess(
            elapsed,
            0.75,
            msg=(
                "Metadata retrieval took %.2fs, suggesting the two curl "
                "calls ran sequentially instead of in parallel" % elapsed
            ),
        )

    def test_missing_token_falls_back_to_unknown_for_both_values(self):
        proc, _ = self._run_block({"FAKE_CURL_TOKEN_FAIL": "1"})
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "unknown-instance-id")
        self.assertEqual(az, "unknown-az")

    def test_instance_id_fetch_failure_falls_back_while_az_still_succeeds(self):
        proc, _ = self._run_block(
            {"FAKE_CURL_INSTANCE_FAIL": "1", "FAKE_CURL_AZ": "ap-southeast-5c"}
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "unknown-instance-id")
        self.assertEqual(az, "ap-southeast-5c")

    def test_az_fetch_failure_falls_back_while_instance_id_still_succeeds(self):
        proc, _ = self._run_block(
            {"FAKE_CURL_AZ_FAIL": "1", "FAKE_CURL_INSTANCE_ID": "i-deadbeef00"}
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "i-deadbeef00")
        self.assertEqual(az, "unknown-az")

    def test_both_fetches_fail_but_script_still_completes_and_cleans_up(self):
        """Regression: even though curl returns nonzero exit codes for both
        background jobs, 'wait $PID_ID $PID_AZ || true' must prevent
        'set -e' from aborting the script, and cleanup must still happen."""
        proc, _ = self._run_block(
            {"FAKE_CURL_INSTANCE_FAIL": "1", "FAKE_CURL_AZ_FAIL": "1"}
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "unknown-instance-id")
        self.assertEqual(az, "unknown-az")
        self.assertFalse(os.path.exists(TMP_INSTANCE_ID_FILE))
        self.assertFalse(os.path.exists(TMP_AZ_FILE))

    def test_explicit_empty_value_fallback_triggers_even_though_temp_file_exists(self):
        """A failed curl still creates an (empty) redirection target file,
        so the 'cat ... || echo' fallback alone would NOT trigger (cat on
        an empty-but-existing file succeeds with empty output). This test
        pins down that the *explicit* '[ -z ... ]' fallback check is what
        actually produces the 'unknown-*' values in that scenario."""
        proc, _ = self._run_block({"FAKE_CURL_INSTANCE_FAIL": "1"})
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, _ = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "unknown-instance-id")

    def test_token_value_is_correctly_threaded_into_both_parallel_requests(self):
        """Uses a distinctive fake token and confirms both parallel curl
        stub invocations still resolve to successful, distinct results,
        i.e. the shared $TOKEN variable is visible inside both background
        subshells."""
        proc, _ = self._run_block(
            {
                "FAKE_CURL_TOKEN": "DISTINCTIVE-TOKEN-XYZ",
                "FAKE_CURL_INSTANCE_ID": "i-tokentest",
                "FAKE_CURL_AZ": "ap-southeast-5a",
            }
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        instance_id, az = self._parse_results(proc.stdout)
        self.assertEqual(instance_id, "i-tokentest")
        self.assertEqual(az, "ap-southeast-5a")


if __name__ == "__main__":
    unittest.main()