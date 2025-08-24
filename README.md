# android-tools-static
android-tools-static is a fork of [nmeum/android-tools][upstream] with the following added features:

- prebuilt executables for a plethora of architectures and operating systems
  - [SBOMs][SBOM] for prebuilt release archives are provided
  - prebuilt executables have minimal external dependencies (they are fully statically linked for Linux targets with the help of [musl libc][musl])
  - several ["layouts"](#release-artifacts) of release archives are provided, some are optimized for best end user experience and some are optimized for embedding in other programs
  - in comparison to official Google release archives, archives provided by this repository are legally redistributable (see [license considerations](license_considerations.md))
- Windows support (taken from [MSYS2][msys2_source])
- nmeum/android-tools' CMake build system is rewritten in Meson
  - external dependencies are handled using Meson's [WrapDB][meson_wraps] system; if they aren't found on the system, they will be automatically downloaded and built alongside android-tools-static (this is fully configurable)

> [!NOTE]
> Testers for MacOS targets would be greatly appreciated, as I do not have the capacity to perform testing myself.
>
> To test android-tools-static, download the latest `android-tools-static-<ver>-macos-nativelayout-universal2.tar.gz` release archive or build the project yourself and test basic functionality (test whether adb push/pull works, whether adb shell works, whether adb install works (not required if your phone blocks such requests), whether adb reboot works, whether fastboot reboot works + anything else you find important). If you need help, feel free to message me through the methods described below.
>
> You can then [start a new discussion](https://github.com/meator/android-tools-static/discussions/new?category=general). If that is not possible for you, you can e-mail me at meator.dev@gmail.com (but please prefer GitHub Discussions if you can, it is not likely that I will notice your e-mail if it ends up in my spam).

# Building
## Build dependencies
- [Meson][meson] version 0.63.0 or higher
- [CMake][cmake]
- `git` or `patch` available (used to patch vendor projects) if you're not using the pre-patched release source archive
- a reasonably recent C++ compiler (C++20 support required, this project might require other more recent features)
- a reasonably recent C compiler (C11 support required, this project might require other more recent features)
- Linux headers (such as `linux/usbdevice_fs.h`, usually provided by a `linux-headers` package) on Linux

This project is buildable with packages from current Debian stable (v12 _bookworm_).

The following dependencies are provided as [Meson Wraps][meson_wraps]. This means that if you do not have these dependencies installed, Meson will download them and build them for you. They are fully configurable using Meson standard flags.

- [libusb][libusb]
- [PCRE][PCRE]
- [Google Test][gtest]
- [protobuf][protobuf]
- [brotli][brotli]
- [zstd][zstd]
- [lz4][lz4]

## Simple build process
Go to the [Releases](https://github.com/meator/android-tools-static/releases) section, download and extract the latest `android-tools-static-<version>-src.tar.gz` archive and build the project as follows:

```sh
meson setup build
meson compile -C build
meson install -C build
```

## Other build configurations
- [I am a packager](docs/packaging.md)
- [I want to build from master](docs/building_from_git.md)

# Release artifacts
This project provides three "flavors" of release artifacts:

1. `standardlayout`

   `standardlayout` archives are best suited for use by other programs and/or libraries, since they provide the same layout for all supported operating systems.

   Here are the guaranteed contents of the archive:

   ```
   android-tools-static/adb
   android-tools-static/append2simg
   android-tools-static/fastboot
   android-tools-static/img2simg
   android-tools-static/simg2img
   ```

   The archive may include extra files (for example `android-tools-static/AdbWinApi.dll` and `android-tools-static/AdbWinUsbApi.dll` on Windows).

   All `standardlayout` release archives are compressed into `.tar.gz` files (even on Windows).

   **All executables do not have a suffix (even on Windows!)** This is done to make the layout more standard.

   The top-level directory in the archive does not include any "dynamic" information (version of the release archive, layout type etc.). The top-level directory is `android-tools-static` on all targets.

   The filenames of the source archives also do not include their version number.
2. `standardlayout-extra`

   `standardlayout-extra` is same as `standardlayout`, but it includes the following additional executables on Linux and MacOS:

   ```
   android-tools-static/lpadd
   android-tools-static/lpdump
   android-tools-static/lpflash
   android-tools-static/lpmake
   android-tools-static/lpunpack
   ```

   If the information above is out of date, please [file an issue](https://github.com/meator/android-tools-static/issues/new).

   The executables above are not included in `standardlayout` because they cannot currently be built for Windows targets.

   This means that `standardlayout` and `standardlayout-extra` release archives for Windows targets will feature comparable contents (they may be identical).
3. `nativelayout`

   This is the layout best suited for end users.

   The top-level directory of the archive includes the release version (unlike `standardlayout` and `standardlayout-extra`).

   Executable files end in `.exe` for Windows targets.

   `nativelayout` release archives are compressed into `.zip` for Windows targets.

   "Miscellaneous" files may be included (manpages, shell completions...).

# Releases

> [!NOTE]
> The maintainers of this repository reserve the right to modify and delete tags published in this repository for 24 hours after their publishing. If a release tag more than two days old, it is safe to use.

Major updates will most likely be bound to the release schedule of [nmeum/android-tools][upstream].

Like [nmeum/android-tools][upstream], android-tools-static follows a

```
<major>.<minor>.<patch>[p<revision>][-rc.<release candidate number>]
```

where `<major>`, `<minor>` and `<patch>` represent the version of android-tools and boringssl being used. If bugfixes needed to be applied to a currently released version, a `p<revision>` suffix is added (examples: `35.0.2`, `35.0.2p1`, `35.0.2p2`...).

Release candidates are denoted with a `-rc.<release candidate number>` suffix. This is an addition to [nmeum/android-tools][upstream]'s versioning system.

## Trusted sources
Here is a list of sources which are trusted during release artifact build:
1. files in this repository (most of which come from the parent project https://github.com/nmeum/android-tools), all the git submodules (coming from official Google repositories), all the Meson wrap dependencies (coming from their official sources with Meson buildsystems and patches from https://github.com/mesonbuild/wrapdb and/or this repository)
2. programs in GitHub official containers (Ubuntu, MacOS and Windows) - mainly pip, brew, MSVC, CMake, Python
3. pinned Meson (and its dependencies) from pip
4. ucrt64, msys and mingw32 MSYS2 official repositories
5. Homebrew official repositories
6. release artifacts of https://github.com/meator/AdbWinApi

Here is a list of trusted GitHub Actions which are trusted (excluding those from <https://github.com/actions>[^actions]):

1. https://github.com/msys2/setup-msys2 - provided officially by MSYS2
2. https://github.com/ilammy/msvc-dev-cmd - used by https://github.com/meator/AdbWinApi, it is less trustworthy than the rest of the GitHub Actions used, but its functionality is very useful and semi-difficult to replace
3. https://github.com/softprops/action-gh-release - the [official GitHub Action which handles making releases](https://github.com/actions/create-release) was deprecated, this action is one of its one of the alternatives mentioned in its README
4. https://github.com/jirutka/setup-alpine - maintained by Alpine Linux developers
5. https://github.com/docker/setup-buildx-action, https://github.com/docker/login-action, https://github.com/docker/metadata-action, https://github.com/docker/bake-action - provided officially by Docker

All the actions listed above are pinned to commit hash of a released version.

# FAQ
## Why rewrite nmeum/android-tools in Meson? Fully static builds can be achieved in CMake with FetchContent or using similar methods.
The main aim of this fork, supporting fully static builds of android-tools, is achievable in CMake. I chose not to simply contribute these changes to nmeum/android-tools for these reasons:

1. I, [meator](https://github.com/meator), have little experience with CMake. I am much more knowledgeable of Meson.
2. [Meson's Wrap][meson_wraps] is (in my opinion) more robust than CMake's solution to the problem.
   1. It is fully controllable by the user (you can use `--force-fallback-for`, `--wrap-mode` etc)
   2. It is forthcoming to packagers (who might not appreciate the build system downloading things at configure time)
   3. It is standard (see the two points above)
   4. They were easy to implement ([wrapdb][wrapdb] contributors did most of the work for me, I could just do `meson wrap install <dep>` to take advantage of it)
   5. Wraps are interchangeable for system installed dependencies
3. Meson adds a lot of nicities (`compile_commands.json` enabled by default, ASAN/UBSAN etc. work without additional configuration, nicer syntax and more)

## What else does android-tools-static add to nmeum/android-tools?
It adds a more customized vendor patching mechanism (nmeum/android-tools one is rather simplistic and strictly requires `git`).

Another focus of this project is improved documentation and UX. The `meson.build` files are already more readable thanks to Meson's intuitive syntax. On top of that, I've tried to add more comments and print customized error messages when common errors are detected.

A lot of effort has been put in to make sure that cross compilation works without problems (since it is used to build release archives for some targets).

## What architecture/OS names do you use?
This project uses the same architecture and OS identifiers used in Meson: https://mesonbuild.com/Reference-tables.html A more human-readable form is sometimes provided in verbose output (for example `x86 (32bit)`, `aarch64 (ARM64)` - ARM64 is the more commonly used name on Windows).

## What version of Windows do I need to use to be able to run Windows prebuilt executables?
Windows 10 or newer is required. See the writeup [here](windows-compatibility.md).

# Credits
This project would not exist without https://github.com/nmeum/android-tools, so thank you [nmeum](https://github.com/nmeum) and nmeum/android-tools contributors!

Windows support is based off of the [MSYS2 package][msys2_pkg] ([source][msys2_source]). Thank you [Biswa96](https://github.com/Biswa96)!

Some patches were taken from [Void Linux][void] and [Chimera Linux][chimera]. Thanks!

# TODO
- [ ] port boringssl to Meson, removing the need for a CMake dependency

      This is pretty hard to do, it might make the most sense to keep the
      CMake dependency for the sake of stability.
- [ ] `fastboot` may require `mke2fs` to function correctly; `mke2fs` isn't currently built by android-tools-static

[^actions]: Actions from https://github.com/actions are considered to be trustworthy and safe; they are not pinned to a commit SHA and they are not included in SBOMs.

[upstream]: https://github.com/nmeum/android-tools
[SBOM]: https://en.wikipedia.org/wiki/Software_supply_chain
[musl]: https://www.musl-libc.org/
[meson]: https://mesonbuild.com/
[meson_wraps]: https://mesonbuild.com/Wrap-dependency-system-manual.html
[wrapdb]: https://github.com/mesonbuild/wrapdb
[cmake]: https://cmake.org/

[libusb]: https://libusb.info/
[PCRE]: https://pcre.sourceforge.net/
[gtest]: https://github.com/google/googletest
[protobuf]: https://github.com/protocolbuffers/protobuf
[brotli]: https://github.com/google/brotli
[zstd]: https://facebook.github.io/zstd/
[lz4]: https://github.com/lz4/lz4

[msys2_pkg]: https://packages.msys2.org/packages/mingw-w64-x86_64-android-tools
[msys2_source]: https://github.com/msys2/MINGW-packages/tree/master/mingw-w64-android-tools
[void]: https://github.com/void-linux/void-packages/tree/master/srcpkgs/android-tools/patches
[chimera]: https://github.com/chimera-linux/cports/tree/master/user/android-tools/patches
