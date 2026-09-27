#!/bin/bash
# Builds the "base" libwineserver.a that build/wineserver/build.sh expects to
# find (it only recompiles ~20 patched files and splices them into an
# existing archive; it never builds wineserver from scratch). No such base
# is tracked in the repo or produced by any other script, so this compiles
# every vanilla wine/server/*.c for iOS arm64 with the same flags
# build/wineserver/build.sh itself uses for its patched files, and archives
# them. Idempotent: skipped if the base archive already exists.
set -e

BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$BUILD_DIR/../.." && pwd)"
WINE_SRC="$REPO_ROOT/wine"
SDK=$(xcrun --sdk iphoneos --show-sdk-path)
APP_LIB="$REPO_ROOT/app/Madeira/libwineserver.a"
SHIMS_DIR="$REPO_ROOT/build/ntdll-unix/shims"
OBJ_DIR="$BUILD_DIR/obj-base"

if [ -f "$APP_LIB" ]; then
    echo "Base libwineserver.a already present, skipping base build."
    exit 0
fi

mkdir -p "$OBJ_DIR"

CC_FLAGS=(
    -arch arm64 -isysroot "$SDK" -miphoneos-version-min=17.0 -O2
    -I"$WINE_SRC/include" -I"$WINE_SRC/include/wine"
    -I"$WINE_SRC/build-macos/include"
    -I"$BUILD_DIR" -I"$WINE_SRC/server"
    -I"$SHIMS_DIR"
    -I"$BUILD_DIR/../madsync" -DHAVE_LINUX_NTSYNC_H=1
    -include "$BUILD_DIR/config_ios.h"
    -include stdarg.h
    -include "$BUILD_DIR/unicode_fix.h"
    -include "$BUILD_DIR/wineserver_ios_kill.h"
    -DBINDIR=\"/usr/local/bin\" -DDATADIR=\"/usr/local/share\"
    -D__WINESRC__ -DWINE_IOS=1
    -Dmain=wineserver_main
    -Wno-implicit-function-declaration
)

FAILED=""
for src in "$WINE_SRC"/server/*.c; do
    name=$(basename "$src" .c)
    echo -n "  [base] $name... "
    if xcrun -sdk iphoneos clang "${CC_FLAGS[@]}" -c "$src" -o "$OBJ_DIR/$name.o" 2>"$OBJ_DIR/err-$name.txt"; then
        echo "OK"
    else
        echo "FAILED"
        cat "$OBJ_DIR/err-$name.txt"
        FAILED="$FAILED $name"
    fi
done

if [ -n "$FAILED" ]; then
    echo "Base build failed for:$FAILED"
    exit 1
fi

ar rcs "$OBJ_DIR/libwineserver.a" "$OBJ_DIR"/*.o
cp "$OBJ_DIR/libwineserver.a" "$APP_LIB"
echo "Base libwineserver.a: $(wc -c < "$APP_LIB" | tr -d ' ') bytes"
