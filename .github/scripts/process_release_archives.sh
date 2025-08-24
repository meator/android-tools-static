#!/bin/bash
set -eu
function handle_archive_universally() {
  if [[ $# -ne 3 ]]; then
    return 1
  fi
  RAW_ARCHIVE_NAME="$1"
  OS="$2"
  ARCH="$3"

  NATIVELAYOUT="android-tools-static-$PROJECT_VERSION-$OS-nativelayout-$ARCH"
  STANDARDLAYOUT="android-tools-static-$OS-standardlayout-$ARCH"
  STANDARDLAYOUTEX="android-tools-static-$OS-standardlayout-extra-$ARCH"

  # Extract the input archive. The contents of this archive are expected to be extracted
  # to android-tools-static/.
  # The contents of this archive are modified and removed from. Archives of all layouts
  # are created during the process.
  tar -oxf "$RAW_ARCHIVE_NAME"

  # x86_64 linux (alpine native) is the source of manpages for all targets.
  # This means that most targets don't have to have a pandoc dependency.
  if [[ "$OS" == "linux" && "$ARCH" == "x86_64" ]]; then
    cp android-tools-static/man1/adb.1 .
  fi

  rm -rf android-tools-static/man1/
  cp adb.1 android-tools-static/

  if [[ "$OS" == "macos" ]]; then
    # macOS universal2 has two SBOMs per archive.
    for sbom_path in android-tools-static/*-SBOM.json; do
      BASENAME="$(basename "$sbom_path")"
      SBOM_ARCH="${BASENAME%-SBOM.json}"
      SBOM_PATH="android-tools-static-$PROJECT_VERSION-$OS-$SBOM_ARCH-SBOM.json"
      mv "$sbom_path" "release-artifacts/$SBOM_PATH"
    done
  else
    # Remove SBOM from the archive, give it an appropriate name and add it
    # to to_release.
    SBOM_PATH="android-tools-static-$PROJECT_VERSION-$OS-$ARCH-SBOM.json"
    mv "android-tools-static/SBOM.json" "release-artifacts/$SBOM_PATH"
  fi

  #
  # nativelayout
  #
  mv android-tools-static "$NATIVELAYOUT"

  if [[ "$OS" == "windows" ]]; then
    zip -r "release-artifacts/$NATIVELAYOUT.zip" "$NATIVELAYOUT"
  else
    tar -czf "release-artifacts/$NATIVELAYOUT.tar.gz" "$NATIVELAYOUT"
  fi

  #
  # standardlayout-extra
  #
  mv "$NATIVELAYOUT" android-tools-static

  rm -rf android-tools-static/bash-completion/
  rm android-tools-static/adb.1

  if [[ "$OS" == "windows" ]]; then
    for executable in android-tools-static/*.exe; do
      mv "$executable" "${executable/.exe}"
    done
  fi

  tar -czf "release-artifacts/$STANDARDLAYOUTEX.tar.gz" android-tools-static

  #
  # standardlayout
  #
  if [[ "$OS" == "windows" ]]; then
    cp "release-artifacts/$STANDARDLAYOUTEX.tar.gz" "release-artifacts/$STANDARDLAYOUT.tar.gz"
  else
    for exe in android-tools-static/*; do
      [[ -x "$exe" ]] || continue
      [[ "$exe" == *".dll" ]] && continue

      # Follow the requirements stated in README.
      BASENAME="$(basename "$exe")"
      if [[ $BASENAME != adb && \
            $BASENAME != append2simg && \
            $BASENAME != fastboot && \
            $BASENAME != img2simg && \
            $BASENAME != simg2img ]]; then
        rm "$exe"
      fi
    done

    tar -czf "release-artifacts/$STANDARDLAYOUT.tar.gz" android-tools-static
  fi
  rm -rf android-tools-static
}

mkdir release-artifacts

handle_archive_universally linux-build-x86_64/android-tools-static-linux-x86_64.tar linux x86_64
for arch in aarch64 ppc64le riscv64 armv6l armv7l; do
  handle_archive_universally linux-build-$arch/android-tools-static-linux-$arch.tar linux $arch
done
handle_archive_universally windows-build-x86_64/android-tools-static-windows-x86_64.tar windows x86_64
handle_archive_universally windows-build-x86/android-tools-static-windows-x86.tar windows x86
handle_archive_universally osx-build/android-tools-static-macos-universal2.tar macos universal2

SOURCE_WIN_AR_NAME="android-tools-static-$PROJECT_VERSION-src-windows"
SOURCE_AR_NAME="android-tools-static-$PROJECT_VERSION-src"

mkdir "$SOURCE_WIN_AR_NAME"
tar -C "$SOURCE_WIN_AR_NAME" -xf source/source.tar
rm -rf "$SOURCE_WIN_AR_NAME"/.git "$SOURCE_WIN_AR_NAME"/vendor/*/.git
find "$SOURCE_WIN_AR_NAME/subprojects" -maxdepth 1 -mindepth 1 -type d \
  ! -name packagefiles ! -name "boringssl-*" ! -name "AdbWinApi-*" \
  -exec rm -rf '{}' +
find "$SOURCE_WIN_AR_NAME/vendor/boringssl" -mindepth 1 -delete
touch "$SOURCE_WIN_AR_NAME/nopatch"

zip -r "release-artifacts/$SOURCE_WIN_AR_NAME.zip" "$SOURCE_WIN_AR_NAME"

mv "$SOURCE_WIN_AR_NAME" "$SOURCE_AR_NAME"
rm -r "$SOURCE_AR_NAME"/subprojects/AdbWinApi-*
tar -czf "release-artifacts/$SOURCE_AR_NAME.tar.gz" "$SOURCE_AR_NAME"
