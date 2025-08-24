# Building from git
The following diagram describes the "clean" build process of android-tools-static:

<div align="center">

![diagram](../etc/Build%20process.svg)

</div>

Here's a transcript of the process:

```sh
# Clone the repo and submodules at once.
# The boringssl submodule isn't technically needed (it is inherited from
# nmeum/android-tools), you do not have to clone it.
git clone --recurse-submodules https://github.com/meator/android-tools-static.git
cd android-tools-static
meson setup build
meson compile -C build
meson install -C build
```

## Release configuration
android-tools-static applies custom configuration when building its prebuilt release artifacts. Most of these changes are contained in `nativefiles/release_configuration*.ini`
