#
# Patch git submodules
#
submodule_patches = {
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
  'boringssl': [
    '0001-boringssl-Add support for loongarch.patch',
    '0001-boringssl-Workaround-compiler-error-with-gcc-14-and-.patch',
    '0012-CMakeLists.txt-Disable-Werror-by-default.patch',
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

  foreach submodule, relative_patch_list: submodule_patches
    patch_list = []
    foreach patch: relative_patch_list
      patch_list += meson.project_source_root() / 'patches' / submodule / patch
    endforeach
    errmsg = run_command(
      files('meson_patch_vendor.py'), git_exe.found() ? git_exe : '', patch_exe.found() ? patch_exe : '', submodule, patch_list,
      check: false,
      # Capture isn't used, but it's nice to have debugging info in Meson logs.
      capture: true,
    )
    if errmsg.returncode() != 0
      error(errmsg.stderr())
    endif
  endforeach
endif

# Meson cannot unfortunatelly subproject() projects not in the subproject/ directory.
# Moving the submodule there would break CMake, symlinking it is problematic
# on Windows, so we just copy it recursively every time.
run_command(
  files('meson_copy_boringssl.py'), meson.project_source_root() / 'vendor' / 'boringssl', meson.project_source_root() / 'subprojects' / 'boringssl',
  check: true,
  capture: false,
)

# TODO
deleteme = find_program('tree')
deleteme2 = find_program('sh')
run_command(
  deleteme2, '-c', 'cd "$1" && "$2"', deleteme2, meson.project_source_root(), deleteme,
  check: true,
  capture: true,
)

#
# boringssl
#
cmake = import('cmake')
boringssl_sub = cmake.subproject('boringssl')
boringssl_crypto = boringssl_sub.dependency('crypto')
boringssl_ssl = boringssl_sub.dependency('ssl')

#
# fmt
#
# TODO: Version requirements.
fmt = dependency('fmt', version: ['>9.1.0', '<=11.0.1'])

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
zstd = dependency('libzstd')

#
# libusb
#
libusb_use_udev = false
if true
  libusb_sources = files(
    'libusb/libusb/core.c',
    'libusb/libusb/descriptor.c',
    'libusb/libusb/hotplug.c',
    'libusb/libusb/io.c',
    'libusb/libusb/sync.c',
    'libusb/libusb/strerror.c',
  )
  if host_machine.system() == 'windows'
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
    if libusb_use_udev
      libusb_sources += files('libusb/libusb/os/linux_udev.c')
    else
      libusb_sources += files('libusb/libusb/os/linux_netlink.c')
    endif
  endif
endif

libusb_args = []
libusb_priv_inc_dirs = ['libusb/libusb', 'libusb/libusb/os']
libusb_deps = []

if host_machine.system() == 'windows'
  libusb_priv_inc_dirs += 'libusb/windows'
elif host_machine.system() == 'darwin'
  libusb_priv_inc_dirs += 'libusb/darwin'

  # TODO: The following dependency detection is in dire need
  #       of further testing!
  libusb_deps += [dependency('CoreFoundation'), dependency('IOKit'), dependency('Security')]
else
  if libusb_use_udev
    libusb_args += '-DHAVE_LIBUDEV'
    libusb_deps += dependency('libudev')
  endif
  libusb_priv_inc_dirs += 'libusb/linux'
endif

android_tools_libusb = static_library(
  'android_tools_libusb',
  libusb_sources,
  include_directories: libusb_priv_inc_dirs,
  c_args: libusb_args,
  dependencies: libusb_deps,
)

#
# libbase
#
libbase_lib = static_library(
  'base',
  'libbase/abi_compatibility.cpp',
  'libbase/chrono_utils.cpp',
  'libbase/cmsg.cpp',
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
  'libbase/errors_unix.cpp',
  include_directories: ['libbase/include', 'core/include', 'logging/liblog/include'],
  dependencies: fmt,
)
# user requires fmt and liblog

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
  # public
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
# adb part 1
#
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
protobuf = dependency('protobuf')

protoc = find_program('protoc', native: true)
adb_proto_sources = []

foreach proto_name: adb_protos
  adb_proto_sources += custom_target(
    # TODO
    command: [protoc, '--cpp_out', '@OUTDIR@', '-I', '@CURRENT_SOURCE_DIR@/adb/proto', '@INPUT@'],
    input: 'adb' / 'proto' / proto_name + '.proto',
    output: [proto_name + '.pb.cc', proto_name + '.pb.h'],
  )
  # TODO: Include builddir containing headers.
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
  'adb/sysdeps_unix.cpp',
  'adb/sysdeps/errno.cpp',
  'adb/sysdeps/posix/network.cpp',
)

libadb_sources += adb_proto_sources

if host_machine.system() == 'darwin'
  libadb_sources += 'adb/client/usb_osx.cpp'
else
  libadb_sources += 'adb/client/usb_linux.cpp'
endif

libadb_includes = [
	'boringssl/include',
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

# TODO if ANDROID_TOOLS_USE_BUNDLED_LIBUSB
if true
  libadb_includes += 'libusb'
  libadb_args += '-DANDROID_TOOLS_USE_BUNDLED_LIBUSB'
endif

libadb_lib = static_library(
  'adb',
  libadb_sources,
  cpp_args: libadb_args,
  include_directories: libadb_includes,
  dependencies: [absl_log, protobuf, brotlicommon, lz4, zstd, gtest]
)

libadb = declare_dependency(
  link_with: libadb_lib,
  compile_args: libadb_args,
  include_directories: libadb_includes,
)

libadb_crypto_defaults_includes = include_directories(
	'adb',
	'adb/crypto/include',
	'boringssl/include',
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
	# TODO
	dependencies: [absl_log, protobuf]
)

libadb_tls_connection_defaults_lib_includes = include_directories(
	'adb',
	'adb/tls/include',
	'boringssl/include',
	'libbase/include',
)

libadb_tls_connection_defaults_lib = static_library(
  'adb_crypto_defaults_includes',
	'adb/tls/adb_ca_list.cpp',
	'adb/tls/tls_connection.cpp',
	include_directories: libadb_tls_connection_defaults_lib_includes,
)

liblog_includes = include_directories(
	'core/include',
	'logging/liblog/include',
	'core/libcutils/include',
	'libbase/include',
)

liblog_lib = static_library(
  'log',
	'logging/liblog/log_event_list.cpp',
	'logging/liblog/log_event_write.cpp',
	'logging/liblog/logger_name.cpp',
	'logging/liblog/logger_read.cpp',
	'logging/liblog/logger_write.cpp',
	'logging/liblog/properties.cpp',
	'logging/liblog/logprint.cpp',
	# TODO: Is -D_XOPEN_SOURCE=700 necessary?
	cpp_args: ['-DLIBLOG_LOG_TAG=1006', '-D_XOPEN_SOURCE=700', '-DFAKE_LOG_DEVICE=1'],
	include_directories: liblog_includes,
)

libcutils_sources = files(
	'core/libcutils/android_get_control_file.cpp',
	'core/libcutils/ashmem-host.cpp',
	'core/libcutils/config_utils.cpp',
	'core/libcutils/fs.cpp',
	'core/libcutils/hashmap.cpp',
	'core/libcutils/iosched_policy.cpp',
	'core/libcutils/load_file.cpp',
	'core/libcutils/multiuser.cpp',
	'core/libcutils/native_handle.cpp',
	'core/libcutils/properties.cpp',
	'core/libcutils/record_stream.cpp',
	'core/libcutils/socket_inaddr_any_server_unix.cpp',
	'core/libcutils/socket_local_client_unix.cpp',
	'core/libcutils/socket_local_server_unix.cpp',
	'core/libcutils/socket_network_client_unix.cpp',
	'core/libcutils/sockets_unix.cpp',
	'core/libcutils/sockets.cpp',
	'core/libcutils/str_parms.cpp',
	'core/libcutils/strlcpy.c',
	'core/libcutils/trace-host.cpp',
)

if host_machine.system() not in ['darwin', 'windows']
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
  # TODO: GNU_SOURCE
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
  # public
  include_directories: ['libbase/include', 'adb'],
)

libcrypto_lib = static_library(
  'crypto',
  'core/libcrypto_utils/android_pubkey.cpp',
  # public
  include_directories: ['core/libcrypto_utils/include', 'boringssl/include'],
)

# absl_log is needed when static linking with forcefallback=true
# because code generated by protoc references it and it for some
# reason doesn't get pulled into the dependency list through other
# means
adb_deps = [libadb, libcutils, libdiagnoseusb, boringssl_crypto, boringssl_ssl, absl_log, protobuf, fmt, brotlicommon, dependency('libbrotlienc'), dependency('libbrotlidec'), lz4, dependency('threads'), zstd, zlib]

if host_machine.system() == 'darwin'
  adb_deps += dependency('appleframeworks', modules: ['CoreFoundation', 'IOKit'])
endif

adb = executable(
  'adb',
  'adb/adb.cpp',
  'adb/adb_io.cpp',
  'adb/adb_listeners.cpp',
  'adb/adb_trace.cpp',
  'adb/adb_unique_fd.cpp',
  'adb/adb_utils.cpp',
  'adb/fdevent/fdevent.cpp',
  'adb/fdevent/fdevent_poll.cpp',
  'adb/fdevent/fdevent_epoll.cpp',
  'adb/shell_service_protocol.cpp',
  'adb/sockets.cpp',
  'adb/socket_spec.cpp',
  'adb/transport.cpp',
  'adb/transport_fd.cpp',
  'adb/client/transport_local.cpp',
  'adb/client/transport_usb.cpp',
  'adb/types.cpp',
  include_directories: ['core/include', 'libbase/include', 'adb', 'core/libcrypto_utils/include', 'boringssl/include', version_header_inc],
  # TODO: libusb
  link_with: [
    libadb_crypto_defaults_lib,
    libadb_tls_connection_defaults_lib,
    libbase_lib,
    libcrypto_lib,
    libadb_sysdeps_lib,
    liblog_lib,
    libzip_lib,
    android_tools_libusb
  ],
  dependencies: adb_deps,
)
