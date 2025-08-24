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

project(
  'android-tools-static',
  'c', 'cpp',
  version: files('VERSION.txt'),
  license: 'Apache-2.0',
  default_options: [
    # android-tools and its dependencies produce a crap ton of warnings.
    # since this project won't attempt to fix them (it is just a build system
    # port), do not enable extensive warnings.
    'warning_level=0',
    'c_std=gnu11',
    'cpp_std=gnu++20',
  ],
  # The protobuf wrap is the wrap which requires the newest Meson.
  # meson_version is set to the highest requirement of any of its wraps.
  meson_version: '>=0.63.0'
)

if meson.get_compiler('cpp').get_id() == 'msvc'
  error(
    'android-tools is not compatible with native MSVC! A Cygwin-like',
    'environmentis needed to compile this project (for example Cygwin, MSYS2).'
  )
endif

if host_machine.endian() == 'big'
  error(
    'One of android-tools\' internal dependencies, BoringSSL, is incompatible',
    'with big endian systems such as ppc and ppc64 (but not ppc64le). Please',
    'see the following link for more info:',
    'https://boringssl.googlesource.com/boringssl/+/9cffd74fdb65c69506a0ce1b19420a67ad0cb19e/include/openssl/target.h#58'
  )
endif

# Android provides it's own version of mke2fs which is incompatible with
# the version shipped by e2fsprogs. To prevent a name clash we install
# androids version of mke2fs under a different name. This name can be
# configured here.
#
# See also: https://bugs.archlinux.org/task/56955
android_mke2fs_name = 'mke2fs.android'

if host_machine.system() == 'darwin'
  add_project_arguments(
    '-D_DARWIN_C_SOURCE', '-D__DARWIN_C_LEVEL=__DARWIN_C_FULL',
    language: ['c', 'cpp']
  )
endif

CXX = meson.get_compiler('cpp')
CC = meson.get_compiler('c')
foreach comp_data: [['c', CC], ['cpp', CXX]]
  lang = comp_data[0]
  comp = comp_data[1]

  if comp.has_argument('-ftrivial-auto-var-init=zero')
    add_project_arguments('-ftrivial-auto-var-init=zero', language: lang)
  else
    if comp.has_multi_arguments(
      '-ftrivial-auto-var-init=zero',
      '-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang'
    )
      add_project_arguments(
        '-ftrivial-auto-var-init=zero',
        '-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang',
        language: lang
      )
    endif
  endif
endforeach

# Android seems to use various attributes supported by clang but not by
# GCC which causes it to emit lots of warnings. Since these attributes
# don't seem to effect runtime behaviour simply disable the warnings.
foreach lang: ['c', 'cpp']
  if meson.get_compiler(lang).get_argument_syntax() == 'gcc'
    add_project_arguments('-Wno-attributes', language: lang)
  endif
endforeach

# libfsmgr (required by fastboot) requires a 64-bit off_t for lseek. On
# 32-bit glibc platforms this is not the case by default.
add_global_arguments(
  '-D_FILE_OFFSET_BITS=64', '-D_LARGEFILE64_SOURCE',
  language: ['c', 'cpp']
)

version_header = files('version.h.in')
subdir('meson')
version_header_inc = include_directories('meson')

subdir('vendor')

subdir('completions')

if get_option('generate_sbom_data')
  nmeum_patches = []
  foreach dirname, patchlist: nmeum_submodule_patches
    foreach patch: patchlist
      nmeum_patches += dirname / patch
    endforeach
  endforeach

  added_patches = []
  foreach dirname, patchlist: added_submodule_patches
    foreach patch: patchlist
      added_patches += dirname / patch
    endforeach
  endforeach

  configure_file(
    command: [
      'SBOM_scripts/save_args.py',
      '@OUTPUT@',
      nmeum_patches
    ],
    install_dir: get_option('licensedir'),
    output: 'nmeum_patches.bin',
  )

  configure_file(
    command: [
      'SBOM_scripts/save_args.py',
      '@OUTPUT@',
      added_patches
    ],
    install_dir: get_option('licensedir'),
    output: 'added_patches.bin',
  )
endif
