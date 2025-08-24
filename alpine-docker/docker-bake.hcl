# https://github.com/docker/metadata-action?tab=readme-ov-file#bake-definition
target "docker-metadata-action" {}

target "_common" {
  args = {
    ALPINE_VERSION = "3.22"
    # A fairly recent version of musl-cross-make is needed. There are multiple
    # features added in newer commits, for example
    # 5b3b4ea504c8b71764d815de76e35c8bc2aaa507, which adds support for Linux
    # kernel 6.15.7. Linux v6 added support for powerpc64 kernel headers.
    # android-tools need kernel headers, so this commit adds support for
    # powerpc64 android-tools.
    MUSL_CROSS_MAKE_VERSION = "3635262e4524c991552789af6f36211a335a77b3"
    BINUTILS_VERSION = "2.44"
    GCC_VERSION = "14.2.0"
    MUSL_VERSION = "1.2.5"
    GMP_VERSION = "6.3.0"
    MPC_VERSION = "1.3.1"
    MPFR_VERSION = "4.2.2"
    LINUX_VERSION = "6.15.7"
    ISL_VERSION = "0.27"
  }
  dockerfile = "universal.Dockerfile"
}

target "aarch64" {
  inherits = ["docker-metadata-action", "_common"]
  args = {
    TARGET_MAK_FILE = "config-aarch64.mak"
  }
  # tags = ["alpine-cross-aarch64"]
}

target "armhf" {
  inherits = ["docker-metadata-action", "_common"]
  args = {
    TARGET_MAK_FILE = "config-armhf.mak"
  }
  # tags = ["alpine-cross-armhf"]
}

target "arm" {
  inherits = ["docker-metadata-action", "_common"]
  args = {
    TARGET_MAK_FILE = "config-arm.mak"
  }
  # tags = ["alpine-cross-arm"]
}

target "powerpc64le" {
  inherits = ["docker-metadata-action", "_common"]
  args = {
    TARGET_MAK_FILE = "config-powerpc64le.mak"
  }
  # tags = ["alpine-cross-powerpc64le"]
}

target "riscv64" {
  inherits = ["docker-metadata-action", "_common"]
  args = {
    TARGET_MAK_FILE = "config-riscv64.mak"
  }
  # tags = ["alpine-cross-riscv64"]
}
