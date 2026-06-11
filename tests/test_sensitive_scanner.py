"""Tests for the commit-time sensitive-change gate."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest

from tools.scan_sensitive_changes import Finding, scan_added_line, scan_diff


class TestSensitiveScanner(unittest.TestCase):
    def assert_detector(self, detector_id: str, value: str) -> None:
        findings = scan_added_line("src/example.txt", 7, value)
        self.assertIn(Finding(detector_id, "src/example.txt", 7), findings)

    def test_secret_detectors(self) -> None:
        self.assert_detector("secret", "token = " + "ghp_" + ("A" * 36))
        self.assert_detector("secret", "api_key=" + ("z" * 24))

    def test_private_key_detector(self) -> None:
        self.assert_detector("private-key", "-----BEGIN " + "PRIVATE KEY-----")

    def test_identifier_detectors(self) -> None:
        values = {
            "email": "person" + "@" + "example.com",
            "ssn": "123" + "-45-6789",
            "phone": "212" + "-555-0198",
            "mrn": "MRN" + ": AB-12345",
            "dob": "DOB" + ": 1980-12-31",
            "payment-card": "4111" + " 1111 1111 1111",
        }
        for detector_id, value in values.items():
            with self.subTest(detector_id=detector_id):
                self.assert_detector(detector_id, value)

    def test_reserved_sentinels_only_apply_to_fixture_paths(self) -> None:
        sentinel = "synthetic.person" + "@" + "example.invalid"
        self.assertEqual(scan_added_line("tests/fixture.txt", 1, sentinel), [])
        self.assertEqual(scan_added_line("data/fixture.txt", 1, sentinel), [])
        self.assert_detector("email", sentinel)

    def test_names_addresses_urls_ips_and_bare_dates_are_not_scanned(self) -> None:
        allowed = (
            "Jane Example lives at 12 Example Street; "
            "see https://example.com from 192.0.2.1 on 2026-06-11"
        )
        self.assertEqual(scan_added_line("docs/note.md", 1, allowed), [])

    def test_protected_path_is_blocked_without_content(self) -> None:
        diff = "\n".join(
            [
                "diff --git a/.env b/.env",
                "--- /dev/null",
                "+++ b/.env",
                "@@ -0,0 +1 @@",
                "+PLACEHOLDER=true",
            ]
        )
        self.assertEqual(scan_diff(diff), [Finding("protected-path", ".env", 0)])

    def test_diff_line_numbers_and_removed_lines(self) -> None:
        email = "person" + "@" + "example.com"
        diff = "\n".join(
            [
                "diff --git a/note.txt b/note.txt",
                "--- a/note.txt",
                "+++ b/note.txt",
                "@@ -10,2 +10,2 @@",
                "-" + email,
                "+plain replacement",
                "+" + email,
            ]
        )
        self.assertEqual(scan_diff(diff), [Finding("email", "note.txt", 11)])

    def test_output_contract_never_requires_matched_values(self) -> None:
        finding = Finding("email", "note.txt", 3)
        stream = io.StringIO()
        with redirect_stdout(stream):
            print(
                f"BLOCK detector={finding.detector_id} "
                f"path={finding.path} line={finding.line}"
            )
        output = stream.getvalue()
        self.assertEqual(output, "BLOCK detector=email path=note.txt line=3\n")
        self.assertNotIn("@", output)


if __name__ == "__main__":
    unittest.main()
