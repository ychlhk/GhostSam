# KernelSU v3.3.1: verified call-site findings

Date: 2026-10-13
Scope: source review only. **No binary rebuilt, tested or deployed.**

## Revisions examined

- Official KernelSU v3.3.1: `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`
- Samsung fork kdp-s26: `0fde5f940559d36c48c9516902b3a7ce944a80c5`

## Confirmed source references

| Concern | Official v3.3.1 | Samsung fork |
| --- | --- | --- |
| Header UAPI version | `uapi/supercall.h:13`, `5` | `uapi/supercall.h:12`, `2` |
| Bundled flag | `uapi/supercall.h:32` | Not declared in inspected header |
| Services event | `uapi/supercall.h:26` | Not declared in inspected header |
| Late-load already-present module check | `userspace/ksud/src/late_load.rs:44` | `userspace/ksud/src/late_load.rs:46` |
| Late-load LKM call | `userspace/ksud/src/late_load.rs:67` | `userspace/ksud/src/late_load.rs:85` |
| Fork-specific daemon staging | Not found at same callsite in inspected official file | `userspace/ksud/src/late_load.rs:43` |

Official source blob hashes:
- `uapi/supercall.h`: `4f6dc48df72393cf082ee7df87ba80a9e9b4d071`
- `userspace/ksud/src/late_load.rs`: `a7434d020984f77f833d752b270738f73004f357`

Fork source blob hashes:
- `uapi/supercall.h`: `e7f9bee70346a6fc166366d8b40ddd447b402c97`
- `userspace/ksud/src/late_load.rs`: `a9824f43239c95e06f48c6b60f253a26a2f824b0`

## Consequences and open questions

- Both sources invoke the KernelSU module loader, but that observation does **not** imply their staged binaries or security-context assumptions are interchangeable.
- The explicit UAPI versions and declarations differ. This establishes an interface mismatch but does not establish which individual runtime calls fail.
- The fork performs a daemon staging step that must be independently assessed for dependency changes.
- The current checker only covers header declarations and Kbuild entries. It does **not** scan all consumers, compare actual ABI symbols, or prove Android device loadability.
- Required before shipping anything: full consumers audit; reproducible compilation provenance; binary metadata inspection; target ABI compatibility tests; and isolated regression testing.

**Release decision: BLOCKED.** Do not represent an updated Manager or successful static scan as a validated Samsung KernelSU v3.3.1 upgrade.
