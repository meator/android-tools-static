# License considerations
Most of android-tools source code is licensed under Apache 2.0. However, the official prebuilt release archives provided by Google appear to have a much stricter license. This may be a concern for developers who wish to bundle android-tools with their programs or libraries because of the following clauses (direct quote from the Android Software Development Kit License Agreement displayed when downloading anything from https://developer.android.com/tools/releases/platform-tools#downloads made on 2025-08-01):

> [...]
> # 3. SDK License from Google
> [...]
> 3.4 You may not use the SDK for any purpose not expressly permitted by the License Agreement. Except to the extent required by applicable third party licenses, you may not copy (except for backup purposes), modify, adapt, redistribute, decompile, reverse engineer, disassemble, or create derivative works of the SDK or any part of the SDK.
> 3.5 Use, reproduction and distribution of components of the SDK licensed under an open source software license are governed solely by the terms of that open source software license and not the License Agreement.
> [...]

I am not a lawyer. I cannot confidently state that the full contents of the release archives provided by Google are licensed under an open source license and thus exempt from 3.4 thanks to 3.5.

One of the reasons I developed this build system port was to produce alternative release archives which are licensed under Apache 2.0 and not under Android Software Development Kit License Agreement to avoid any possible issues.
