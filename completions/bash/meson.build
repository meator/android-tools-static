cfg = configuration_data()
cfg.set('COMPLETION_COMMON_DIR', 'fixme')

foreach file: ['adb', 'fastboot']
  configure_file(
    input: f'@file@.in',
    output: f'@file@',
    configuration: cfg,
    install: true,
    format: 'cmake@',
    install_dir: get_option('datadir') / 'bash-completion/completions',
  )
endforeach
