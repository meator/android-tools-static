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

vendor_cfg = configuration_data()

# Vendor string used in version outputs.
vendor_cfg.set('ANDROID_VENDOR', 'android-tools-static')

configure_file(
  input: version_header,
  output: 'version.h',
  configuration: vendor_cfg,
  format: 'cmake@',
)
