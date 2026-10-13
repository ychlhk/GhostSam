# KernelSU UAPI 3 scoped su-session review

Reviewed 2026-10-13. Official upstream `tiann/KernelSU@v3.3.1` and Samsung fork `snothin/KernelSU@kdp-s26`.

## Key finding

**The Samsung fork has the scoped su-session kernel implementation even while its header advertises UAPI 2.** Therefore the UAPI numeric gap should not be treated as proof that all UAPI 3 behavior is missing.

Verified in both revisions:
- `kernel/supercall/supercall.c`: `KSU_DRIVER_PERMISSION_SU_SESSION` defined (line 20), `ksu_install_su_fd()` (line 89), returns FD with scoped permission (line 92), and `ksu_is_su_session_fd()` (line 95).
- `kernel/supercall/dispatch.c`: two ioctl handler entries set `allow_su_session = true` (upstream lines 826,863; fork lines 801,838), with scoped permission check in dispatch (upstream line 886; fork line 861).
- Official `uapi/supercall.h` declares UAPI **5**, Samsung fork declares **2**.

Blob identities:
- Upstream `kernel/supercall/supercall.c`: `6db2649565895020ac7429b004c503ff7165f146`.
- Samsung fork `kernel/supercall/supercall.c`: `c35ce87368f1bdacbb15e37f18fd05c83bf3cc1c`.
- Upstream `kernel/supercall/dispatch.c`: `82ac7003032a5a16af04e47311d6a4b4ee1ab814`.
- Samsung fork `kernel/supercall/dispatch.c`: `9c1874a2ad04f385707de4330967e33b73e86ef2`.

## Interpretation

- UAPI 3 scoped-session functionality is visibly represented in both kernel trees; exact runtime equivalence still unproven.
- Existing CI gate comparing only the UAPI version appropriately flags inconsistent advertised versions, but its failure **does not prove lack of scoped-session support**.
- Consumer and behavioral tests remain necessary; do not simply change the UAPI constant to 5.

Status: source review only. No privileged loading or binary modification.
