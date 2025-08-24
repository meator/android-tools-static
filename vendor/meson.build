# Copyright 2025 meator
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# Patch git submodules
#
nmeum_submodule_patches = {
  'adb': [
    '0001-Don-t-use-the-internal-glibc-header-sys-cdefs.h.patch',
    '0002-adb-disable-mdns-transport-support.patch',
    '0003-adb-include-missing-headers.patch',
    '0004-Define-clang-only-nullability-specifiers-when-__clan.patch',
    '0005-Include-libusb-1.0-libusb.h-instead-of-libusb-libusb.patch',
    '0006-Include-string.h-in-various-file-missing-it.patch',
    '0007-adb-Fix-unknown-__xx_write-member-in-std-ostream.patch',
    '0008-adb-Disable-bonjour-check.patch',
    '0009-adb-Reduce-fallback-size-for-_SC_GETPW_R_SIZE_MAX.patch',
    '0010-sysdeps-don-t-over-eager-constexpr.patch',
    '0013-adb-disable-fastdeploy-support.patch',
    '0015-types.h-Fix-ambiguous-reference-to-weak_ptr.patch',
    '0016-adb-disable-mDNS.patch',
    '0017-adb_wifi-remove-mDNS.patch',
    '0020-Fix-compilation-with-libusb-1.0.24.patch',
    '0023-Update-usage-of-usbdevfs_urb-to-match-new-kernel-UAP.patch',
    '0026-Drop-compile-static-check.patch',
  ],
  'core': [
    '0001-Fix-inclusion-of-stdatomic.h-with-g.patch',
    '0004-fastboot-make-mke2fs_path-configurable.patch',
    '0009-Don-t-use-the-internal-glibc-header-sys-cdefs.h.patch',
    '0011-core-include-missing-headers.patch',
    '0012-Add-explicit-import-for-algorithm.patch',
  ],
  'extras': [
    '0001-Don-t-use-the-internal-glibc-header-sys-cdefs.h.patch',
    '0002-libjsonpbparse-Fix-build-after-protobuf-util-Status-.patch',
    '0003-extras-libjsonpb-Fix-incompatibility-with-protobuf-v.patch',
  ],
  'libbase': [
    '0001-android-base-endian.h-fix-build-on-musl.patch',
    '0002-remove-glibc-internal-headers-cdefs.h.patch',
    '0003-logging.h-only-activate-ostream-warnings-when-clang-.patch',
    '0004-Don-t-use-thread-safety-annotations-with-gcc.patch',
    '0006-remove-usage-of-__builtin_available.patch',
  ],
  'libziparchive': [
    '0001-remove-glibc-internal-header-cdefs.h.patch',
  ],
  'logging': [
    '0001-Don-t-use-the-internal-glibc-header-sys-cdefs.h.patch',
    '0002-Fix-inclusion-of-stdatomic.h-with-g.patch',
    '0004-fix-initializer-element-is-not-constant-error-when-b.patch',
  ],
}

added_submodule_patches = {
  'adb': [
    '0027-Add-support-for-Meson-Wrap-libusb-include.patch',
    '0028-WIN-fix-compilation.patch',
    '0029-WIN-fix-pointer-casting.patch',
  ],
  'libziparchive': [
    '0002-WIN-fix-static-assert-failure.patch',
  ],
}

fs = import('fs')
# Assume that vendored projects are patched already if the 'nopatch'
# file exists in the source root. Useful in release archives which
# include pre-fetched and pre-patched submodules.
# The build system will never create, modify or delete this file.
nopatch = fs.exists(meson.project_source_root() / 'nopatch')

if nopatch
  git_exe = disabler()
else
  git_exe = find_program('git', required: false)
  if git_exe.found()
    patch_exe = disabler()
  else
    patch_exe = find_program('patch', required: false)
  endif

  if not git_exe.found() and not patch_exe.found()
    error(
      'Both \'git\' and \'patch\' are not available in the build environment!',
      'The build system needs a way to patch git submodules. See Meson logs for',
      'more info.'
    )
  endif

  if git_exe.found() and fs.exists(meson.project_source_root() / '.git')
    run_command(
      git_exe, 'submodule', '--quiet', 'update',
      capture: false,
      check: true,
    )
  endif

  foreach patch_series: [nmeum_submodule_patches, added_submodule_patches]
    foreach submodule, relative_patch_list: patch_series
      patch_list = []
      foreach patch: relative_patch_list
        patch_list += meson.project_source_root() / 'patches' / submodule / patch
      endforeach
      errmsg = run_command(
        files('meson_patch_vendor.py'), git_exe.found() ? git_exe : '',
        patch_exe.found() ? patch_exe : '', submodule, patch_list,
        check: false,
        # Capture isn't used, but it's nice to have debugging info in Meson logs.
        capture: true,
      )
      if errmsg.returncode() != 0
        error(errmsg.stderr())
      endif
    endforeach
  endforeach
endif

# If you want to only patch the vendor directories and do not want to actually
# set up anything, you can uncommend the line below. This is used in the GitHub
# Actions runner. It is padded by comments to produce a nice independent patch
# with the context lines containing only comments.

#subdir_done()

# See above.
# See above.
# See above.
# See above.

adbwinapi_deps = []

#
# AdbWinApi
#
if host_machine.system() in ['cygwin', 'windows']
  adbwinapi_deps += dependency('AdbWinApi')
endif

#
# boringssl
#
cmake = import('cmake')

boringssl_opts = cmake.subproject_options()
# Meson's cmake module is limited. It doesn't seem to handle ASM building in
# cross/i686 native well. The check below is likely too restrictive, but it's
# better to err on the side of caution. This problem could be resolved by
# porting boringssl to Meson (this is one of the TODO entries in README).
if meson.is_cross_build() or host_machine.cpu_family() != 'x86_64'
  boringssl_opts.add_cmake_defines({'OPENSSL_NO_ASM': true})
endif
boringssl_sub = cmake.subproject('boringssl', options: boringssl_opts)
boringssl_crypto = boringssl_sub.get_variable('crypto_dep')
boringssl_ssl = boringssl_sub.get_variable('ssl_dep')

boringssl_crypto_inc_dep = boringssl_crypto.partial_dependency(includes: true)

#
# fmt
#
fmt = dependency('fmt', version: '>9.1.0')

#
# zlib
#
zlib = dependency('zlib')

#
# brotli
#
brotlicommon = dependency('libbrotlicommon')

#
# lz4
#
lz4 = dependency('liblz4')

#
# zstd
#
zstd = dependency('libzstd', default_options: 'bin_programs=false')

#
# libusb
#
if get_option('use_bundled_libusb')
  udev_dep = dependency('', required: false)
  libusb_sources = files(
    'libusb/libusb/core.c',
    'libusb/libusb/descriptor.c',
    'libusb/libusb/hotplug.c',
    'libusb/libusb/io.c',
    'libusb/libusb/sync.c',
    'libusb/libusb/strerror.c',
  )
  if host_machine.system() in ['cygwin', 'windows']
    libusb_sources += files(
      'libusb/libusb/os/events_windows.c',
      'libusb/libusb/os/threads_windows.c',
      'libusb/libusb/os/windows_common.c',
      'libusb/libusb/os/windows_usbdk.c',
      'libusb/libusb/os/windows_winusb.c',
    )
  elif host_machine.system() == 'darwin'
    libusb_sources += files(
      'libusb/libusb/os/events_posix.c',
      'libusb/libusb/os/darwin_usb.c',
      'libusb/libusb/os/threads_posix.c',
    )
  else
    libusb_sources += files(
      'libusb/libusb/os/events_posix.c',
      'libusb/libusb/os/linux_usbfs.c',
      'libusb/libusb/os/threads_posix.c',
    )
    udev_dep = dependency('libudev', required: get_option('libusb_enable_udev'))
    if udev_dep.found()
      libusb_sources += files('libusb/libusb/os/linux_udev.c')
    else
      libusb_sources += files('libusb/libusb/os/linux_netlink.c')
    endif
  endif

  libusb_args = []
  libusb_priv_inc_dirs = ['libusb/libusb', 'libusb/libusb/os']
  libusb_private_deps = []
  libusb_deps = []

  if host_machine.system() in ['cygwin', 'windows']
    libusb_priv_inc_dirs += 'libusb/windows'
  elif host_machine.system() == 'darwin'
    libusb_priv_inc_dirs += 'libusb/darwin'

    # TODO: The following dependency detection is in dire need
    #       of further testing!
    libusb_private_deps += dependency(
      'appleframeworks',
      modules: ['CoreFoundation', 'IOKit', 'Security']
    )
  else
    if udev_dep.found()
      libusb_args += '-DHAVE_LIBUDEV'
      libusb_deps += udev_dep
    endif
    libusb_priv_inc_dirs += 'libusb/linux'
  endif

  android_tools_libusb = static_library(
    'android_tools_libusb',
    libusb_sources,
    include_directories: libusb_priv_inc_dirs,
    c_args: libusb_args,
    dependencies: libusb_private_deps + libusb_deps,
  )
  libusb_dep = declare_dependency(
    link_with: android_tools_libusb,
    dependencies: libusb_deps,
  )
else
  feature = get_option('libusb_enable_udev')
  if feature.enabled()
    udev = 'enabled'
  elif feature.disabled()
    udev = 'disabled'
  elif feature.auto()
    udev = 'auto'
  endif
  libusb_dep = dependency(
    'libusb-1.0',
    default_options: ['udev=' + udev, 'examples=false', 'tests=false']
  )
endif

#
# libbase
#
libbase_sources = [
  'libbase/abi_compatibility.cpp',
  'libbase/chrono_utils.cpp',
  'libbase/file.cpp',
  'libbase/hex.cpp',
  'libbase/logging.cpp',
  'libbase/mapped_file.cpp',
  'libbase/parsebool.cpp',
  'libbase/parsenetaddress.cpp',
  'libbase/posix_strerror_r.cpp',
  'libbase/process.cpp',
  'libbase/properties.cpp',
  'libbase/result.cpp',
  'libbase/stringprintf.cpp',
  'libbase/strings.cpp',
  'libbase/threads.cpp',
  'libbase/test_utils.cpp',
]

if host_machine.system() in ['cygwin', 'windows']
  libbase_sources += [
    'libbase/errors_windows.cpp',
    'libbase/utf8.cpp',
  ]
else
  libbase_sources += [
    'libbase/cmsg.cpp',
    'libbase/errors_unix.cpp',
  ]
endif

libbase_lib = static_library(
  'base',
  libbase_sources,
  # vendor/libbase/posix_strerror_r.cpp requires access to non-GNU version
  # of strerror_r() which is exposed if (_POSIX_C_SOURCE >= 200112L) && ! _GNU_SOURCE
  # The source file makes sure that _GNU_SOURCE is not defined.
  cpp_args: '-D_POSIX_C_SOURCE=200112L',
  include_directories: [
    'libbase/include',
    'core/include',
    'logging/liblog/include'
  ],
  dependencies: fmt,
)

#
# fastboot part 1 (libzip)
#
gtest = dependency('gtest')

libzip_lib = static_library(
  'zip',
  'libziparchive/zip_archive.cc',
  'libziparchive/zip_archive_stream_entry.cc',
  'libziparchive/zip_cd_entry_map.cc',
  'libziparchive/zip_error.cpp',
  'libziparchive/zip_writer.cc',
  cpp_args: '-DZLIB_CONST',
  include_directories: [
    'libziparchive/include',
    'libziparchive/incfs_support/include',
    'core/include',
    'logging/liblog/include',
    'libbase/include',
  ],
  dependencies: [zlib, gtest],
)

#
# adb
#
pandoc_exe = find_program('pandoc', required: get_option('generate_manpages'))
if pandoc_exe.found()
  custom_target(
    command: [
      pandoc_exe, '--standalone', '--to=man', '@INPUT@', '--output', '@OUTPUT@'
    ],
    input: 'adb/docs/user/adb.1.md',
    output: 'adb.1',
    install: true,
    install_dir: get_option('mandir') / 'man1',
  )
endif

adb_protos = [
  'app_processes',
  'adb_host',
  'key_type',
  'adb_known_hosts',
  'pairing',
]

absl_log = dependency('absl_log')

# protobuf library dependency needs to be resolved before find_program('protoc')
# is run.
# If protoc is not installed, the following dependency() call will pull the
# protobuf wrap which will override the 'protoc' executable. If the dependency()
# would be called later, the wrap's attempt to override the possibly already
# found 'protoc' would cause a configuration error.
raw_protobuf_dep = dependency('protobuf', default_options: 'install=false')

# BEGIN CODE SECTION
# This code section can be dropped once https://github.com/mesonbuild/wrapdb/pull/2331
# is merged
if meson.version().version_compare('>=1.7.0')
  atomic_dep = dependency(
    'atomic',
    required: false,
  )
else
  atomic_dep = meson.get_compiler('cpp').find_library(
    'atomic',
    required: false,
  )
endif

# Make reasonable effort (volatile) to prevent the compiler from optimizing the
# atomic away without using tested functionality.
if not meson.get_compiler('cpp').links(
  '''
#include <atomic>
#include <cstdint>
int main() {
    volatile std::atomic<std::uint64_t> testvar;
    // The line below will lead to
    // undefined reference to `__atomic_fetch_add_8'
    // on armv6l to give an example.
    volatile auto unused = testvar.fetch_add(0);
}
  ''',
  name: 'Check if libatomic is required',
  dependencies: atomic_dep,
)
  error('Host machine cannot handle atomics!')
endif

protobuf = declare_dependency(
  dependencies: [raw_protobuf_dep, atomic_dep]
)
# END CODE SECTION

protoc = find_program('protoc', native: true)
adb_proto_sources = []

foreach proto_name: adb_protos
  adb_proto_sources += custom_target(
    command: [
      protoc,
      '--cpp_out',
      '@OUTDIR@',
      '-I',
      '@CURRENT_SOURCE_DIR@/adb/proto',
      '@INPUT@'
    ],
    input: 'adb' / 'proto' / proto_name + '.proto',
    output: [proto_name + '.pb.cc', proto_name + '.pb.h'],
  )
endforeach

libadb_sources = files(
  'adb/client/adb_client.cpp',
  'adb/client/adb_install.cpp',
  'adb/client/adb_wifi.cpp',
  'adb/client/auth.cpp',
  'adb/client/bugreport.cpp',
  'adb/client/commandline.cpp',
  'adb/client/console.cpp',
  'adb/client/file_sync_client.cpp',
  'adb/client/incremental.cpp',
  'adb/client/incremental_server.cpp',
  'adb/client/incremental_utils.cpp',
  'adb/client/line_printer.cpp',
  'adb/client/main.cpp',
  'adb/client/pairing/pairing_client.cpp',
  'adb/client/usb_libusb.cpp',
  'adb/pairing_auth/aes_128_gcm.cpp',
  'adb/pairing_auth/pairing_auth.cpp',
  'adb/pairing_connection/pairing_connection.cpp',
  'adb/services.cpp',
  'adb/socket_spec.cpp',
  'adb/sysdeps/errno.cpp',
)

libadb_sources += adb_proto_sources

if host_machine.system() in ['cygwin', 'windows']
  libadb_sources += [
    'adb/client/usb_windows.cpp',
    'adb/sysdeps_win32.cpp',
    'adb/sysdeps/win32/errno.cpp',
    'adb/sysdeps/win32/stat.cpp',
  ]
elif host_machine.system() == 'darwin'
  libadb_sources += [
    'adb/client/usb_osx.cpp',
    'adb/sysdeps_unix.cpp',
    'adb/sysdeps/posix/network.cpp',
  ]
else
  libadb_sources += [
    'adb/client/usb_linux.cpp',
    'adb/sysdeps_unix.cpp',
    'adb/sysdeps/posix/network.cpp',
  ]
endif

libadb_includes = [
  'adb',
  'adb/crypto/include',
  'adb/pairing_auth/include',
  'adb/pairing_connection/include',
  'adb/tls/include',
  'core/include',
  'core/libcrypto_utils/include',
  'core/libcutils/include',
  'libbase/include',
  'libziparchive/include',
]

libadb_args = ['-DADB_HOST=1']
libadb_private_args = ['-D_GNU_SOURCE']

if get_option('use_bundled_libusb')
  libadb_includes += 'libusb'
  libadb_args += '-DANDROID_TOOLS_USE_BUNDLED_LIBUSB'
endif

if host_machine.system() in ['cygwin', 'windows']
  libadb_private_args += [
    '-DUNICODE',
    '-D_UNICODE',
    '-D_POSIX',
    '-D_POSIX_SOURCE'
  ]
endif

libadb_lib = static_library(
  'adb',
  libadb_sources,
  cpp_args: libadb_args + libadb_private_args,
  include_directories: libadb_includes,
  dependencies: [
    absl_log,
    protobuf,
    brotlicommon,
    lz4,
    zstd,
    gtest,
    libusb_dep,
    boringssl_crypto_inc_dep,
    adbwinapi_deps
  ]
)

libadb = declare_dependency(
  link_with: libadb_lib,
  compile_args: libadb_args,
  include_directories: libadb_includes,
)

libadb_crypto_defaults_includes = include_directories(
  'adb',
  'adb/crypto/include',
  'core/libcrypto_utils/include',
  'libbase/include',
)

libadb_crypto_defaults_lib = static_library(
  'adb_crypto_defaults',
  'adb/crypto/key.cpp',
  'adb/crypto/rsa_2048_key.cpp',
  'adb/crypto/x509_generator.cpp',
  adb_proto_sources,
  include_directories: libadb_crypto_defaults_includes,
  dependencies: [absl_log, protobuf, boringssl_crypto_inc_dep]
)

libadb_tls_connection_defaults_lib_includes = include_directories(
  'adb',
  'adb/tls/include',
  'libbase/include',
)

libadb_tls_connection_defaults_lib = static_library(
  'adb_crypto_defaults_includes',
  'adb/tls/adb_ca_list.cpp',
  'adb/tls/tls_connection.cpp',
  include_directories: libadb_tls_connection_defaults_lib_includes,
  dependencies: boringssl_crypto_inc_dep
)

liblog_includes = include_directories(
  'core/include',
  'logging/liblog/include',
  'core/libcutils/include',
  'libbase/include',
)

liblog_private_args = []

if host_machine.system() in ['cygwin', 'windows']
  liblog_private_args += '-DWIN32_LEAN_AND_MEAN'
endif

liblog_lib = static_library(
  'log',
  'logging/liblog/log_event_list.cpp',
  'logging/liblog/log_event_write.cpp',
  'logging/liblog/logger_name.cpp',
  'logging/liblog/logger_read.cpp',
  'logging/liblog/logger_write.cpp',
  'logging/liblog/properties.cpp',
  'logging/liblog/logprint.cpp',
  cpp_args: [
    '-DLIBLOG_LOG_TAG=1006',
    '-D_XOPEN_SOURCE=700',
    '-DFAKE_LOG_DEVICE=1'
  ] + liblog_private_args,
  include_directories: liblog_includes,
)

libcutils_sources = files(
  'core/libcutils/config_utils.cpp',
  'core/libcutils/iosched_policy.cpp',
  'core/libcutils/load_file.cpp',
  'core/libcutils/native_handle.cpp',
  'core/libcutils/properties.cpp',
  'core/libcutils/record_stream.cpp',
  'core/libcutils/sockets.cpp',
  'core/libcutils/strlcpy.c',
)

if host_machine.system() in ['cygwin', 'windows']
  libcutils_sources += [
    'core/libcutils/socket_inaddr_any_server_windows.cpp',
    'core/libcutils/socket_network_client_windows.cpp',
    'core/libcutils/sockets_windows.cpp',
  ]
else
  libcutils_sources += [
    'core/libcutils/android_get_control_file.cpp',
    'core/libcutils/ashmem-host.cpp',
    'core/libcutils/fs.cpp',
    'core/libcutils/hashmap.cpp',
    'core/libcutils/multiuser.cpp',
    'core/libcutils/socket_inaddr_any_server_unix.cpp',
    'core/libcutils/socket_local_client_unix.cpp',
    'core/libcutils/socket_local_server_unix.cpp',
    'core/libcutils/socket_network_client_unix.cpp',
    'core/libcutils/sockets_unix.cpp',
    'core/libcutils/str_parms.cpp',
    'core/libcutils/trace-host.cpp',
  ]
endif

if host_machine.system() not in ['darwin', 'cygwin', 'windows']
  libcutils_sources += files(
    'core/libcutils/canned_fs_config.cpp',
    'core/libcutils/fs_config.cpp',
  )
endif

libcutils_public_includes = include_directories(
  'core/libcutils/include',
  'libbase/include',
)

libcutils_lib = static_library(
  'cutils',
  libcutils_sources,
  include_directories: [
    'logging/liblog/include',
    'core/libutils/include',
    libcutils_public_includes,
  ]
)

libcutils = declare_dependency(
  link_with: libcutils_lib,
  include_directories: libcutils_public_includes,
)

libdiagnoseusb_includes = include_directories(
  'core/diagnose_usb/include',
  'core/include',
  'libbase/include',
)

libdiagnoseusb_lib = static_library(
  'cutils_public_includes',
  'core/diagnose_usb/diagnose_usb.cpp',
  include_directories: libdiagnoseusb_includes
)

libdiagnoseusb = declare_dependency(
  link_with: libdiagnoseusb_lib,
  include_directories: libdiagnoseusb_includes
)

libadb_sysdeps_lib = static_library(
  'adb_sysdeps_lib',
  'adb/sysdeps/env.cpp',
  include_directories: ['libbase/include', 'adb'],
)

libcrypto_lib = static_library(
  'crypto',
  'core/libcrypto_utils/android_pubkey.cpp',
  include_directories: [
    'core/libcrypto_utils/include',
  ],
  dependencies: boringssl_crypto_inc_dep,
)

# absl_log is needed when static linking with forcefallback=true
# because code generated by protoc references it and it for some
# reason doesn't get pulled into the dependency list through other
# means
adb_deps = [
  libadb,
  libcutils,
  libdiagnoseusb,
  boringssl_crypto,
  boringssl_ssl,
  absl_log,
  protobuf,
  fmt,
  brotlicommon,
  dependency('libbrotlienc'),
  dependency('libbrotlidec'),
  lz4,
  dependency('threads'),
  zstd,
  zlib,
  libusb_dep
]

if host_machine.system() == 'darwin'
  adb_deps += dependency('appleframeworks', modules: ['CoreFoundation', 'IOKit'])
endif

adb_sources = [
  'adb/adb.cpp',
  'adb/adb_io.cpp',
  'adb/adb_listeners.cpp',
  'adb/adb_trace.cpp',
  'adb/adb_unique_fd.cpp',
  'adb/adb_utils.cpp',
  'adb/fdevent/fdevent.cpp',
  'adb/fdevent/fdevent_poll.cpp',
  'adb/shell_service_protocol.cpp',
  'adb/sockets.cpp',
  'adb/socket_spec.cpp',
  'adb/transport.cpp',
  'adb/transport_fd.cpp',
  'adb/client/transport_local.cpp',
  'adb/client/transport_usb.cpp',
  'adb/types.cpp',
  adb_proto_sources,
]

adb_args = []
adb_ld_args = []

if host_machine.system() in ['cygwin', 'windows']
  adb_args += ['-D_GNU_SOURCE', '-D_POSIX', '-D_POSIX_SOURCE']
  adb_deps += [
    adbwinapi_deps,
    meson.get_compiler('cpp').find_library('ws2_32'),
  ]
  adb_ld_args += '-municode'
else
  adb_sources += 'adb/fdevent/fdevent_epoll.cpp'
endif

executable(
  'adb',
  adb_sources,
  cpp_args: adb_args,
  link_args: adb_ld_args,
  include_directories: [
    'core/include',
    'libbase/include',
    'adb',
    'core/libcrypto_utils/include',
    version_header_inc
  ],
  link_with: [
    libadb_crypto_defaults_lib,
    libadb_tls_connection_defaults_lib,
    libbase_lib,
    libcrypto_lib,
    libadb_sysdeps_lib,
    liblog_lib,
    libzip_lib,
  ],
  dependencies: [adb_deps, boringssl_crypto_inc_dep],
  install: true,
)

#
# sparse
#
libsparse_inc = include_directories(
  'core/libsparse/include',
  'libbase/include',
)
libsparse_lib = static_library(
  'sparse',
  'core/libsparse/backed_block.cpp',
  'core/libsparse/output_file.cpp',
  'core/libsparse/sparse.cpp',
  'core/libsparse/sparse_crc32.cpp',
  'core/libsparse/sparse_err.cpp',
  'core/libsparse/sparse_read.cpp',
  include_directories: libsparse_inc,
  link_with: libbase_lib,
  dependencies: zlib,
)
libsparse = declare_dependency(
  link_with: libsparse_lib,
  include_directories: libsparse_inc,
)

executable(
  'simg2img',
  'core/libsparse/simg2img.cpp',
  dependencies: [libsparse, zlib],
  link_with: libbase_lib,
  install: true,
)

executable(
  'img2simg',
  'core/libsparse/img2simg.cpp',
  dependencies: [libsparse, zlib],
  link_with: libbase_lib,
  install: true,
)

append2simg_args = []
if host_machine.system() in ['cygwin', 'windows']
  append2simg_args += '-D_GNU_SOURCE'
endif

executable(
  'append2simg',
  'core/libsparse/append2simg.cpp',
  cpp_args: append2simg_args,
  dependencies: [libsparse, zlib],
  link_with: libbase_lib,
  install: true,
)

#
# fastboot part 2 (libext4)
#
libext4_inc = include_directories(
  'core/libsparse/include',
  'core/include',
  'selinux/libselinux/include',
  'extras/ext4_utils/include',
  'libbase/include',
)
libext4_lib = static_library(
  'ext4',
  'extras/ext4_utils/ext4_utils.cpp',
  'extras/ext4_utils/wipe.cpp',
  'extras/ext4_utils/ext4_sb.cpp',
  include_directories: libext4_inc,
)
libext4 = declare_dependency(
  link_with: libext4_lib,
  include_directories: libext4_inc,
)

#
# partition
#
liblp_inc = 'core/fs_mgr/liblp/include'
liblp_lib = static_library(
  'lp',
  'core/fs_mgr/liblp/builder.cpp',
  'core/fs_mgr/liblp/super_layout_builder.cpp',
  'core/fs_mgr/liblp/images.cpp',
  'core/fs_mgr/liblp/partition_opener.cpp',
  'core/fs_mgr/liblp/property_fetcher.cpp',
  'core/fs_mgr/liblp/reader.cpp',
  'core/fs_mgr/liblp/utility.cpp',
  'core/fs_mgr/liblp/writer.cpp',
  link_with: libbase_lib,
  dependencies: [
    libext4, libsparse, boringssl_crypto, zlib, boringssl_crypto_inc_dep
  ],
  include_directories: [
    liblp_inc
  ],
)
liblp = declare_dependency(
  link_with: liblp_lib,
  include_directories: liblp_inc,
)

if host_machine.system() not in ['cygwin', 'windows']
  libjsonpbparse_inc = include_directories(
    'extras/libjsonpb/parse/include',
    # Added include:
    'libbase/include',
  )
  libjsonpbparse_deps = [dependency('absl_status'), protobuf]
  libjsonpbparse_lib = static_library(
    'jsonpbparse',
    'extras/libjsonpb/parse/jsonpb.cpp',
    link_with: libbase_lib,
    dependencies: libjsonpbparse_deps,
    include_directories: libjsonpbparse_inc,
  )
  libjsonpbparse = declare_dependency(
    link_with: libjsonpbparse_lib,
    dependencies: libjsonpbparse_deps,
    include_directories: libjsonpbparse_inc,
  )

  dynamic_partitions_device_info_proto = custom_target(
    command: [
      protoc,
      '--cpp_out',
      '@OUTDIR@',
      '-I', '@CURRENT_SOURCE_DIR@/extras/partition_tools',
      '@INPUT@'
    ],
    input: 'extras/partition_tools/dynamic_partitions_device_info.proto',
    output: [
      'dynamic_partitions_device_info.pb.cc',
      'dynamic_partitions_device_info.pb.h'
    ],
  )

  liblpdump_lib = static_library(
    'lpdump',
    'extras/partition_tools/lpdump.cc',
    dynamic_partitions_device_info_proto,
    link_with: libbase_lib,
    dependencies: [libjsonpbparse, liblp, protobuf],
  )

  executable(
    'lpdump',
    'extras/partition_tools/lpdump_host.cc',
    link_with: [libbase_lib, liblpdump_lib, liblog_lib],
    dependencies: [libsparse, protobuf],
    install: true,
  )

  executable(
    'lpmake',
    'extras/partition_tools/lpmake.cc',
    link_with: [libbase_lib, liblog_lib],
    dependencies: [liblp, libsparse, fmt],
    install: true,
  )

  executable(
    'lpadd',
    'extras/partition_tools/lpadd.cc',
    link_with: [libbase_lib, liblog_lib],
    dependencies: [liblp, libsparse],
    install: true,
  )
  executable(
    'lpflash',
    'extras/partition_tools/lpflash.cc',
    link_with: [libbase_lib, liblog_lib],
    dependencies: [liblp, libsparse],
    install: true,
  )
  executable(
    'lpunpack',
    'extras/partition_tools/lpunpack.cc',
    link_with: [libbase_lib, liblog_lib],
    dependencies: [liblp, libsparse],
    install: true,
  )
endif

#
# fastboot part 3 (the rest of fastboot)
#
libutil_inc = include_directories(
  'core/include',
  'logging/liblog/include',
  'core/libutils/include',
  'libbase/include',
)
libutil_lib = static_library(
  'util',
  'core/libutils/FileMap.cpp',
  include_directories: libutil_inc,
)
libutil = declare_dependency(
  link_with: libutil_lib,
  include_directories: libutil_inc,
)

if host_machine.system() not in ['cygwin', 'windows']
  libselinux_args = [
    '-DAUDITD_LOG_TAG=1003',
    '-D_GNU_SOURCE',
    '-DBUILD_HOST',
    '-DUSE_PCRE2',
    '-DNO_PERSISTENTLY_STORED_PATTERNS',
    '-DDISABLE_SETRANS',
    '-DDISABLE_BOOL',
    '-DNO_MEDIA_BACKEND',
    '-DNO_X_BACKEND',
    '-DNO_DB_BACKEND',
    '-DPCRE2_CODE_UNIT_WIDTH=8',
  ]
  if meson.get_compiler('c').has_header_symbol('string.h', 'strlcpy')
    libselinux_args += '-DHAVE_STRLCPY'
  endif
  libselinux_inc = include_directories(
    'selinux/libselinux/include',
    'selinux/libsepol/include',
  )
  libselinux_lib = static_library(
    'selinux',
    'selinux/libselinux/src/booleans.c',
    'selinux/libselinux/src/callbacks.c',
    'selinux/libselinux/src/freecon.c',
    'selinux/libselinux/src/label_backends_android.c',
    'selinux/libselinux/src/label.c',
    'selinux/libselinux/src/label_support.c',
    'selinux/libselinux/src/matchpathcon.c',
    'selinux/libselinux/src/setrans_client.c',
    'selinux/libselinux/src/sha1.c',
    'selinux/libselinux/src/label_file.c',
    'selinux/libselinux/src/regex.c',
    c_args: libselinux_args,
    dependencies: dependency(
      'libpcre2-8',
      default_options: ['test=false', 'grep=false']
    ),
    include_directories: libselinux_inc,
  )
  libselinux = declare_dependency(
    link_with: libselinux_lib,
    include_directories: libselinux_inc,
  )

  libsepol_args = [
    # vendor/selinux/libsepol/src/context.c and possibly more source files
    # require access to strdup. There are multiple feature test macros
    # which make it available, the most universal seems to be
    '-D_XOPEN_SOURCE=500',
    # reallocarray() requires _DEFAULT_SOURCE since glibc 2.29
    '-D_DEFAULT_SOURCE',
  ]
  if meson.get_compiler('c').has_header_symbol('stdlib.h', 'reallocarray')
    libsepol_args += '-DHAVE_REALLOCARRAY'
  endif
  libsepol_inc = include_directories(
    'selinux/libsepol/include',
  )
  libsepol_lib = static_library(
    'sepol',
    'selinux/libsepol/src/assertion.c',
    'selinux/libsepol/src/avrule_block.c',
    'selinux/libsepol/src/avtab.c',
    'selinux/libsepol/src/conditional.c',
    'selinux/libsepol/src/constraint.c',
    'selinux/libsepol/src/context.c',
    'selinux/libsepol/src/context_record.c',
    'selinux/libsepol/src/debug.c',
    'selinux/libsepol/src/ebitmap.c',
    'selinux/libsepol/src/expand.c',
    'selinux/libsepol/src/hashtab.c',
    'selinux/libsepol/src/hierarchy.c',
    'selinux/libsepol/src/kernel_to_common.c',
    'selinux/libsepol/src/mls.c',
    'selinux/libsepol/src/policydb.c',
    'selinux/libsepol/src/policydb_convert.c',
    'selinux/libsepol/src/policydb_public.c',
    'selinux/libsepol/src/services.c',
    'selinux/libsepol/src/sidtab.c',
    'selinux/libsepol/src/symtab.c',
    'selinux/libsepol/src/util.c',
    'selinux/libsepol/src/write.c',
    'selinux/libsepol/src/optimize.c',
    c_args: libsepol_args,
    include_directories: libsepol_inc,
  )
  libsepol = declare_dependency(
    link_with: libsepol_lib,
    include_directories: libsepol_inc,
  )
endif

fastboot_src = files(
  'core/fastboot/bootimg_utils.cpp',
  'core/fastboot/fastboot.cpp',
  'core/fastboot/fastboot_driver.cpp',
  'core/fastboot/filesystem.cpp',
  'core/fastboot/fs.cpp',
  'core/fastboot/main.cpp',
  'core/fastboot/socket.cpp',
  'core/fastboot/storage.cpp',
  'core/fastboot/super_flash_helper.cpp',
  'core/fastboot/task.cpp',
  'core/fastboot/tcp.cpp',
  'core/fastboot/udp.cpp',
  'core/fastboot/vendor_boot_img_utils.cpp',
  'core/fastboot/util.cpp',
)

if host_machine.system() in ['cygwin', 'windows']
  fastboot_src += files('core/fastboot/usb_windows.cpp')
elif host_machine.system() == 'darwin'
  fastboot_src += files('core/fastboot/usb_osx.cpp')
else
  fastboot_src += files('core/fastboot/usb_linux.cpp')
endif

fastboot_inc = [
  'libbase/include',
  'core/include',
  # The following directories do not exist:
  # 'core/adb',
  # 'core/libziparchive/include',
  # Here is a fixed version of the dir above:
  'libziparchive/include',
  'core/libsparse/include',
  'extras/ext4_utils/include',
  'extras/f2fs_utils',
  'mkbootimg/include/bootimg',
  'core/fs_mgr/liblp/include',
  'core/fs_mgr/libstorage_literals',
  'avb',
  version_header_inc,
]

fastboot_args = [
  '-D_GNU_SOURCE',
  '-D_XOPEN_SOURCE=700',
  '-DUSE_F2FS',
  f'-DANDROID_MKE2FS_NAME="@android_mke2fs_name@"',
]

if host_machine.system() in ['cygwin', 'windows']
  fastboot_args += '-DWIN32_LEAN_AND_MEAN'
endif

fastboot_deps = [
  libsparse,
  libcutils,
  liblp,
  libutil,
  libext4,
  libdiagnoseusb,
  boringssl_crypto,
  zlib,
  dependency('libpcre2-8'),
  dependency('threads'),
  fmt,
  gtest,
  adbwinapi_deps
]

if host_machine.system() in ['cygwin', 'windows']
  fastboot_deps += meson.get_compiler('cpp').find_library('ws2_32')
else
  fastboot_deps += [libselinux, libsepol, dependency('dl')]
endif

if host_machine.system() == 'darwin'
  fastboot_deps += dependency(
    'appleframeworks',
    modules: ['CoreFoundation', 'IOKit']
  )
endif

executable(
  'fastboot',
  fastboot_src,
  cpp_args: fastboot_args,
  link_with: [libzip_lib, liblog_lib, libbase_lib],
  include_directories: [fastboot_inc],
  dependencies: fastboot_deps,
  install: true,
)
