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

if __name__ == "__main__":
    unittest.main()
