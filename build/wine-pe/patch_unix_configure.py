#!/usr/bin/env python3
"""CI-only fixups so the wine submodule's `configure`/makedep step succeeds.
The fork's loader.c #includes a companion file that was never added to the
tree; makedep scans #include text statically regardless of #ifdef guards, so
it errors out even though the guarded branch (__arm64ec__) never compiles on
this host. Add a minimal, always-safe stub so dependency generation succeeds;
the guarded branch only actually builds for the arm64ec-windows PE target."""
import sys, os
wine = sys.argv[1]
path = os.path.join(wine, "dlls/ntdll/arm64ec_x64_export_iat.c")
if not os.path.exists(path):
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
else:
    print("already present:", path)


def fix_include_order(wine):
    """makedep requires config.h to be the literal first #include; these two
    files put a local header first (to dodge Wine's strncpy poison macro,
    which only appears later via windef.h/winbase.h -- so swapping the two
    lines keeps that protection while satisfying makedep)."""
    import re
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

if __name__ == "__main__":
    fix_include_order(sys.argv[1])
