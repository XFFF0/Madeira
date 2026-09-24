#!/usr/bin/env python3
"""CI-only source fixups for the FEX submodule so it compiles as the iOS static lib
(Windows-only diagnostics leaked into non-Windows code paths). Idempotent."""
import sys
p = sys.argv[1] + "/FEXCore/Source/Utils/ArchHelpers/Arm64.cpp"
s = open(p).read()
old_start = "  MEMORY_BASIC_INFORMATION mbi {};\n  const char* type = \"?\";\n"
i = s.find(old_start)
if i >= 0:
    j = s.find("  LogMan::Msg::EFmt(\"[caspal128] MISALIGNED-UNSUPPORTED", i)
    new = ("  struct { void* BaseAddress; size_t RegionSize; uint32_t Protect; uint32_t State; } mbi {};\n"
           "  const char* type = \"?\"; /* VirtualQuery diagnostic is Windows-only; omitted on iOS host */\n")
    s = s[:i] + new + s[j:]
    open(p, "w").write(s)
    print("patched Arm64.cpp")
else:
    print("Arm64.cpp: nothing to patch")
