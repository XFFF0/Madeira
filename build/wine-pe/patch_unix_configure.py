#!/usr/bin/env python3
"""CI-only fixups to the wine submodule so `configure`/makedep and the custom
unix-lib builds (build/ntdll-unix, win32u-unix, wineserver) succeed. The wine
submodule is an external fork we don't own, so these are applied at CI time
rather than committed there. Idempotent."""
import sys, os

def stub_missing_arm64ec_export_iat(wine):
    """loader.c #includes a companion file that was never added to the tree;
    makedep scans #include text statically regardless of #ifdef guards, so it
    errors out even though the guarded branch (__arm64ec__) never compiles on
    this host. Minimal, always-safe stub so dependency generation succeeds."""
    path = os.path.join(wine, "dlls/ntdll/arm64ec_x64_export_iat.c")
    if os.path.exists(path):
        print("already present:", path)
        return
    with open(path, "w") as f:
        f.write(
"""/* CI stub: conservative fallback (see build/wine-pe/patch_unix_configure.py).
 * Always reports "not a preserved x64 export slot" -> native path is used. */
static BOOL arm64ec_iat_slot_is_x64_export( HMODULE module, ULONG image_size, ULONG_PTR slot_rva,
                                             ULONG_PTR export_dir_rva, ULONG export_size,
                                             ULONG code_map, ULONG code_map_count )
{
    return FALSE;
}
""")
    print("created stub:", path)

def fix_include_order(wine):
    """makedep requires config.h to be the literal first #include; these two
    files put a local header first (to dodge Wine's strncpy poison macro,
    which only appears later via windef.h/winbase.h -- so swapping the two
    lines keeps that protection while satisfying makedep)."""
    for rel in ("dlls/ntdll/unix/sync.c", "dlls/ntdll/unix/system.c"):
        p = os.path.join(wine, rel)
        if not os.path.exists(p):
            continue
        s = open(p).read()
        old = '#include "../../../../build/madeira_cfg.h"   /* ml1122: before the Wine headers, which ban strncpy by macro */\n#include "config.h"\n'
        new = '#include "config.h"\n#include "../../../../build/madeira_cfg.h"   /* ml1122: before the Wine headers, which ban strncpy by macro; after config.h, which makedep requires first */\n'
        if old in s:
            open(p, "w").write(s.replace(old, new))
            print("fixed include order:", p)

def add_gamepad_call_code(wine):
    """build/win32u-unix/sysparams_ios.c and driver_ios.c reference
    NtUserCallTwoParam_GetGamepadState, a custom NtUserCallTwoParam code for
    the iOS XInput plumbing, but no one ever added it to the shared enum in
    ntuser.h. Nothing else in this tree currently passes this code, so
    appending it is safe."""
    path = os.path.join(wine, "include/ntuser.h")
    s = open(path).read()
    old = "    NtUserCallTwoParam_GetVirtualScreenRect,\n    /* temporary exports */\n"
    new = "    NtUserCallTwoParam_GetVirtualScreenRect,\n    NtUserCallTwoParam_GetGamepadState,\n    /* temporary exports */\n"
    if old in s:
        open(path, "w").write(s.replace(old, new))
        print("added NtUserCallTwoParam_GetGamepadState:", path)
    elif "NtUserCallTwoParam_GetGamepadState" in s:
        print("already present:", path)
    else:
        print("WARNING: could not locate insertion point in", path)

if __name__ == "__main__":
    wine = sys.argv[1]
    stub_missing_arm64ec_export_iat(wine)
    fix_include_order(wine)
    add_gamepad_call_code(wine)
