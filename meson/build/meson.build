vendor_cfg = configuration_data()

# Vendor string used in version outputs.
vendor_cfg.set('ANDROID_VENDOR', 'android-tools')

configure_file(
  input: version_header,
  output: 'version.h',
  configuration: vendor_cfg,
  format: 'cmake@',
)
