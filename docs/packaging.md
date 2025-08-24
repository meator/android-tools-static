# Build instructions for packagers
This project, like the parent [nmeum/android-tools][upstream_repo] project, is structured in a fairly nonstandard way, so please pay attention to the advice below.

android-tools-static fetches several git submodules which come from official Google repositories, applies a plethora of patches on top of them and then proceeds to build android-tools as a single project.

Google internal dependencies cannot be split from android-tools, because these dependencies often rely on each other, which then forms dependency loops. This is amplified by Google's [Monorepo][monorepo] source code management strategy.

The `android-tools-static-<ver>-src.tar.gz` custom release archive bundles all necessary submodules. They come pre-patched. A special `nopatch` file is included at the root of the archive which tells the build system to skip the patch applying phase. It is recommended for packagers to use this release archive.

Apart from the remarks laid out above, this project follows standard Meson build procedure.

## Windows
A separate `android-tools-static-<ver>-src-windows.zip` source archive is provided for the convenience of Windows users/packagers. This archive differs from `android-tools-static-<ver>-src.tar.gz` in the following ways:

1. it is archived using ZIP
2. it bundles the [AdbWinApi][adbwinapi_repo] Wrap, which is a dependency of android-tools-static on Windows

[AdbWinApi][adbwinapi_repo] currently doesn't support any dependency discovery methods (it doesn't provide a pkg-config file, CMake discovery files or anything else). This may be subject to change in the future. This Wrap must therefore be downloaded and used as a Wrap. Other Wraps aren't included in the release archives, as they can be replaced with system installed dependencies.

## Bug reporting
Please feel free to report any FTBFS issues on standard and/or nonstandard system configurations. This project aims to support as many architectures, libcs etc. as possible.

[upstream_repo]: https://github.com/nmeum/android-tools
[monorepo]: https://en.wikipedia.org/wiki/Monorepo
[adbwinapi_repo]: https://github.com/meator/AdbWinApi
