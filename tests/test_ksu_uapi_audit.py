"""Unit tests for the read-only KernelSU source audit."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_kernelsu_uapi.py"
spec = importlib.util.spec_from_file_location("ksu_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class AuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "uapi").mkdir()
        (self.root / "kernel").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, header, kbuild="kernelsu-objs := core/init.o\n"):
        (self.root / "uapi" / "supercall.h").write_text(header)
        (self.root / "kernel" / "Kbuild").write_text(kbuild)

    def test_uapi_2_no_new_flags(self):
        self.write("static const __u32 KERNEL_SU_UAPI_VERSION = 2;\n")
        out = audit.inspect(self.root)
        self.assertEqual(out["uapi"], 2)
        self.assertFalse(out["bundled_flag"])
        self.assertFalse(out["services_event"])

    def test_uapi_5_features_detected(self):
        self.write(
            "static const __u32 KERNEL_SU_UAPI_VERSION = 5;\n"
            "static const __u32 KSU_GET_INFO_FLAG_BUNDLED = (1U << 4);\n"
            "static const __u32 EVENT_SERVICES = 4;\n",
            "kernelsu-objs += compat/samsung_kdp.o\n"
            "kernelsu-objs += compat/samsung_defex.o\n",
        )
        out = audit.inspect(self.root)
        self.assertTrue(out["bundled_flag"])
        self.assertTrue(out["services_event"])
        self.assertTrue(out["samsung_kdp_object"])
        self.assertTrue(out["samsung_defex_object"])

    def test_missing_version_fails(self):
        self.write("/* no defined uapi version */\n")
        with self.assertRaises(SystemExit):
            audit.inspect(self.root)

    def test_missing_source_fails(self):
        (self.root / "kernel" / "Kbuild").unlink(missing_ok=True)
        with self.assertRaises(SystemExit):
            audit.inspect(self.root)


    def test_mismatched_uapi_fails_when_gate_enabled(self):
        import subprocess
        import sys
        upstream = self.root / "upstream"
        fork = self.root / "fork"
        for source, version in ((upstream, 5), (fork, 2)):
            (source / "uapi").mkdir(parents=True)
            (source / "kernel").mkdir()
            (source / "uapi" / "supercall.h").write_text(
                f"static const __u32 KERNEL_SU_UAPI_VERSION = {version};\n"
            )
            (source / "kernel" / "Kbuild").write_text("kernelsu-objs := core/init.o\n")
        output = self.root / "report"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--upstream", str(upstream),
             "--fork", str(fork), "--output", str(output), "--fail-on-mismatch"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertTrue((output / "report.json").is_file())
        self.assertTrue((output / "report.md").is_file())


    def test_matching_uapi_gate_does_not_fail(self):
        import subprocess
        import sys
        upstream = self.root / "matched_upstream"
        fork = self.root / "matched_fork"
        for source in (upstream, fork):
            (source / "uapi").mkdir(parents=True)
            (source / "kernel").mkdir()
            (source / "uapi" / "supercall.h").write_text(
                "static const __u32 KERNEL_SU_UAPI_VERSION = 5;\\n".replace("\\n", "\n")
            )
            (source / "kernel" / "Kbuild").write_text("kernelsu-objs := core/init.o\n")
        output = self.root / "matched_report"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--upstream", str(upstream),
             "--fork", str(fork), "--output", str(output), "--fail-on-mismatch"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((output / "report.json").is_file())


    def test_optional_callsite_inspection(self):
        self.write("static const __u32 KERNEL_SU_UAPI_VERSION = 5;\n")
        (self.root / "kernel" / "supercall").mkdir()
        (self.root / "userspace" / "ksud" / "src").mkdir(parents=True)
        (self.root / "kernel" / "supercall" / "supercall.c").write_text(
            "int ksu_install_su_fd(void); bool ksu_is_su_session_fd(void);\n"
        )
        (self.root / "kernel" / "supercall" / "dispatch.c").write_text(
            "allow_su_session; KSU_GET_INFO_FLAG_BUNDLED; case EVENT_SERVICES: break;\n"
        )
        (self.root / "userspace" / "ksud" / "src" / "ksucalls.rs").write_text(
            "event: ksu_uapi::EVENT_SERVICES,\n"
        )
        out = audit.inspect(self.root)
        self.assertTrue(out["uapi3_scoped_session_kernel"])
        self.assertTrue(out["uapi4_bundled_dispatch"])
        self.assertTrue(out["uapi5_services_dispatch"])
        self.assertTrue(out["uapi5_services_userspace"])

    def test_unavailable_optional_files_are_unknown(self):
        self.write("static const __u32 KERNEL_SU_UAPI_VERSION = 2;\n")
        out = audit.inspect(self.root)
        self.assertIsNone(out["uapi3_scoped_session_kernel"])
        self.assertIsNone(out["uapi4_bundled_dispatch"])
        self.assertIsNone(out["uapi5_services_dispatch"])
        self.assertIsNone(out["uapi5_services_userspace"])


    def test_same_version_missing_feature_is_blocked(self):
        import subprocess
        import sys
        import json
        upstream = self.root / "feature_upstream"
        fork = self.root / "feature_fork"
        for source in (upstream, fork):
            (source / "uapi").mkdir(parents=True)
            (source / "kernel" / "supercall").mkdir(parents=True)
            (source / "uapi" / "supercall.h").write_text(
                "static const __u32 KERNEL_SU_UAPI_VERSION = 5;\n"
            )
            (source / "kernel" / "Kbuild").write_text("kernelsu-objs := core/init.o\n")
        (upstream / "kernel" / "supercall" / "dispatch.c").write_text(
            "cmd.flags |= KSU_GET_INFO_FLAG_BUNDLED;\n"
        )
        (fork / "kernel" / "supercall" / "dispatch.c").write_text(
            "/* feature absent */\n"
        )
        output = self.root / "feature_report"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--upstream", str(upstream),
             "--fork", str(fork), "--output", str(output), "--fail-on-mismatch"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        report = json.loads((output / "report.json").read_text())
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("uapi4_bundled_dispatch", report["missing_source_features"])

if __name__ == "__main__":
    unittest.main()
