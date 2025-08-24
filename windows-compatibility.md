# Windows compatibility
Attempts have been made to support Windows versions older than Windows 10. These attempts have been unsuccessful.

## Why?
I do not know whether adb advertises Windows 10 as its minimum supported version. I don't think that adb or its internal dependencies would have a hard dependency on features introduced in Windows 10, I find it more likely that adb and its internal dependencies use general Windows functionality, most of which is compatible with old Windows releases. But some features require newer Windows releases "unintentionally" because developers did not test for older Windows releases, and they used what's available.

If that's the case, it shouldn't be _that_ hard to apply appropriate patches which would either remove or replace functionality not available in older Windows releases.

Even though android-tools-static includes many patches for internal dependencies, I am hesitant to add more to enable compatibility with older Windows versions, especially when they would require more intrusive changes to the codebase (which may or may not be necessary).

If you would like to see support for versions of Windows older than Windows 10, please make your voice heard at https://github.com/meator/android-tools-static/discussions/1

## Current blocker
Here is the reason why `adb.exe` currently doesn't run on Windows 7 (and likely older versions of Windows). This is the "primary error", solving it may uncover other ones.

`abort()` is called [here](https://boringssl.googlesource.com/boringssl/+/9cffd74fdb65c69506a0ce1b19420a67ad0cb19e/crypto/rand_extra/windows.c#70) in BoringSSL internal dependency of android-tools. This is caused by the `ProcessPrng` function not being provided by the `bcryptprimitives` library. The `ProcessPrng` function was introduced in Windows 8[^processprng].

Trace[^offset]:
```
Call Site
ucrtbase!abort
adb!init_processprng [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\rand_extra\windows.c @ 69]
adb!pthread_once [\builddir\cross-x86_64-w64-mingw32-12.0.0\mingw-w64-v12.0.0\mingw-w64-libraries\winpthreads\src\thread.c @ 1026]
adb!CRYPTO_MUTEX_unlock_write [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\thread_pthread.c @ 51]
adb!init_processprng [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\rand_extra\windows.c @ 71]
adb!init_processprng [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\rand_extra\windows.c @ 71]
adb!CRYPTO_sysrand [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\rand_extra\windows.c @ 82]
adb!rand_get_seed [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rand\rand.c @ 328]
adb!RAND_bytes_with_additional_data [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rand\rand.c @ 392]
adb!RAND_bytes [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rand\rand.c @ 481]
adb!BN_rand [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\bn\random.c @ 161]
adb!generate_prime [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rsa\rsa_impl.c @ 984]
adb!rsa_generate_key_impl [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rsa\rsa_impl.c @ 1151]
adb!RSA_generate_key_ex_maybe_fips [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rsa\rsa_impl.c @ 1275]
adb!RSA_generate_key_ex [\android-tools-static\subprojects\boringssl-9cffd74fdb65c69506a0ce1b19420a67ad0cb19e\crypto\fipsmodule\rsa\rsa_impl.c @ 1321]
adb!adb::crypto::CreateRSA2048Key [\android-tools-static\vendor\adb\crypto\rsa_2048_key.cpp @ 57]
adb!generate_key [\android-tools-static\vendor\adb\client\auth.cpp @ 67]
adb!load_userkey [\android-tools-static\vendor\adb\client\auth.cpp @ 221]
adb!adb_auth_init [\android-tools-static\vendor\adb\client\auth.cpp @ 418]
adb!adb_server_main [\android-tools-static\vendor\adb\client\main.cpp @ 180]
adb!adb_commandline [\android-tools-static\vendor\adb\client\commandline.cpp @ 1721]
adb!main [\android-tools-static\vendor\adb\client\main.cpp @ 241]
adb!wmain [\android-tools-static\vendor\adb\sysdeps_win32.cpp @ 2916]
adb!__tmainCRTStartup [\builddir\cross-x86_64-w64-mingw32-12.0.0\mingw-w64-v12.0.0\mingw-w64-crt\crt\crtexe.c @ 268]
adb!mainCRTStartup [\builddir\cross-x86_64-w64-mingw32-12.0.0\mingw-w64-v12.0.0\mingw-w64-crt\crt\crtexe.c @ 190]
kernel32!BaseThreadInitThunk
ntdll!RtlUserThreadStart
```

[^processprng]: https://learn.microsoft.com/en-us/windows/win32/seccng/processprng#requirements
[^offset]: The top of the stacktrace may be off by a few lines. The functions called are correct.
