project(
  'android-tools',
  'c', 'cpp',
  # Version of android-tools and the version of boringssl being used.
  # See: https://android.googlesource.com/platform/external/boringssl/+/platform-tools-${ANDROID_VERSION}/BORINGSSL_REVISION
  version: '35.0.2',
  default_options: [
    'warning_level=3',
    'c_std=gnu11',
    'cpp_std=gnu++20',
  ],
)

if host_machine.system() == 'darwin'
  add_project_arguments('-D_DARWIN_C_SOURCE', '-D__DARWIN_C_LEVEL=__DARWIN_C_FULL', language: 'c')
  add_project_arguments('-D_DARWIN_C_SOURCE', '-D__DARWIN_C_LEVEL=__DARWIN_C_FULL', language: 'cpp')
endif

CXX = meson.get_compiler('cpp')
CC = meson.get_compiler('c')
foreach comp_data: [['c', CC], ['cpp', CXX]]
  lang = comp_data[0]
  comp = comp_data[1]

  if comp.has_argument('-ftrivial-auto-var-init=zero')
    add_project_arguments('-ftrivial-auto-var-init=zero', language: lang)
  else
    if comp.has_multi_arguments('-ftrivial-auto-var-init=zero', '-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang')
      add_project_arguments('-ftrivial-auto-var-init=zero', '-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang', language: lang)
    endif
  endif
endforeach

# Android seems to use various attributes supported by clang but not by
# GCC which causes it to emit lots of warnings. Since these attributes
# don't seem to effect runtime behaviour simply disable the warnings.
add_project_arguments('-Wno-attributes', language: 'c')
add_project_arguments('-Wno-attributes', language: 'cpp')

# libfsmgr (required by fastboot) requires a 64-bit off_t for lseek. On
# 32-bit glibc platforms this is not the case by default.
add_global_arguments('-D_FILE_OFFSET_BITS=64', '-D_LARGEFILE64_SOURCE', language: 'c')
add_global_arguments('-D_FILE_OFFSET_BITS=64', '-D_LARGEFILE64_SOURCE', language: 'cpp')

subdir('completions/bash')

version_header = files('version.h.in')
subdir('meson')
version_header_inc = include_directories('meson')

subdir('vendor')
#dependency('avb')
#dependency('libbase')
#dependency('adb')
