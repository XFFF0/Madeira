#!/bin/bash
# Configure (first time) and build the FEXCore static libraries the app links
# (FEX/build-ios/FEXCore/Source/*.a and External/*). Options mirror the
# development build's CMakeCache.
set -eu
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
B="$R/FEX/build-ios"
python3 "$R/build/fex-ios/patch.py" "$R/FEX"
if [ ! -f "$B/CMakeCache.txt" ]; then
    cmake -S "$R/FEX" -B "$B" -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_SYSTEM_PROCESSOR=arm64 -DCMAKE_OSX_ARCHITECTURES=arm64 \
        -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_DEPLOYMENT_TARGET=17.0 -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=OFF -DBUILD_THUNKS=OFF -DBUILD_FEXCONFIG=OFF -DBUILD_FEX_LINUX_TESTS=OFF \
        -DENABLE_FEX_ALLOCATOR=OFF -DENABLE_ASSERTIONS=OFF -DENABLE_CLANG_THUNKS=ON -DENABLE_CCACHE=ON -DTUNE_CPU=none \
        -DCMAKE_C_FLAGS=-DFEX_IOS_HOST=1 -DCMAKE_CXX_FLAGS=-DFEX_IOS_HOST=1 -DCMAKE_ASM_FLAGS=-DFEX_IOS_HOST=1
fi
cmake --build "$B" --target FEXCore FEXCore_Base
ls "$B/FEXCore/Source/"*.a

# The Xcode project also links these FEX-vendored static libs directly.
# Building the two targets above normally pulls them in as link
# dependencies, but don't gamble on that: build each by name if its
# archive isn't already on disk.
declare -A EXTRA_LIBS=(
    [External/SoftFloat-3e/libsoftfloat_3e.a]=softfloat_3e
    [External/cephes/libcephes_128bit.a]=cephes_128bit
    [External/fmt/libfmt.a]=fmt
    [External/xxhash/cmake_unofficial/libxxhash.a]=xxhash
    [FEXCore/Source/libJemallocLibs.a]=JemallocLibs
)
for rel in "${!EXTRA_LIBS[@]}"; do
    if [ ! -f "$B/$rel" ]; then
        echo "Missing $rel, building target ${EXTRA_LIBS[$rel]}..."
        cmake --build "$B" --target "${EXTRA_LIBS[$rel]}" || echo "WARN: target ${EXTRA_LIBS[$rel]} build failed; Xcode link will report this if it's actually needed"
    fi
    [ -f "$B/$rel" ] && echo "OK: $rel" || echo "STILL MISSING: $rel (check the CMake target name in FEX/CMakeLists.txt / External/*)"
done
