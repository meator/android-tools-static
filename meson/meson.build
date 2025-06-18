version_cfg = configuration_data()

# Vendor string used in version outputs.
version_cfg.set('ANDROID_VERSION', meson.project_version())

configure_file(
  input: '../platform_tools_version.h.in',
  output: 'platform_tools_version.h',
  configuration: version_cfg,
  format: 'cmake@',
)

subdir('build')
