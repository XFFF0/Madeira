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
