# KernelSU v3.3.1 UAPI 4/5 implementation audit

Reviewed 2026-10-13. Exact revisions: upstream `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`; Samsung fork `0fde5f940559d36c48c9516902b3a7ce944a80c5`.

| Behavior | Upstream v3.3.1 | Samsung fork |
| --- | --- | --- |
| Bundled flag in GET_INFO | `kernel/supercall/dispatch.c` lines 46–47, 77–78 | No corresponding occurrence in the inspected file |
| Services event state tracking | `kernel/supercall/dispatch.c` lines 103, 115, 145–150 | No corresponding occurrence in the inspected file |
| Userspace services event caller | `userspace/ksud/src/ksucalls.rs` lines 227–229 | No corresponding occurrence in the inspected file |

Source blobs reviewed:
- Official dispatch: `82ac7003032a5a16af04e47311d6a4b4ee1ab814`
- Samsung dispatch: `9c1874a2ad04f385707de4330967e33b73e86ef2`
- Official ksucalls: `37fdecc3d1f739e592df9909a59a8b86356f770c`
- Samsung ksucalls: `a844ddd1b08cbb09f1cd8b8bc555cab340dcdf2d`

## Finding
Unlike UAPI 3 (whose scoped-session functions were observed in both trees), the inspected Samsung dispatch and ksud caller files do not contain the new UAPI 4 bundled-reporting and UAPI 5 service-event references. This is direct file-level evidence, not a global proof of absence or an end-to-end runtime test.

**Release gate remains BLOCKED:** upgrading UAPI version constants cannot supply the associated kernel/userspace semantics. Further review must validate the changes' interactions with Samsung's customized late-load behavior and branch-specific security features.

No executable code, privilege escalation mechanism, binary payload, or phone state has been modified in this review.
