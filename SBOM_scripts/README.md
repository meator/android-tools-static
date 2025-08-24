# SBOM generation
This directory includes a small independent Python project used for generating SBOMs.

All Python source files in this directory do not have any external dependencies except for Python standard library.

The SBOM generation mechanism has four entrypoint scripts:

```
alpine_cross.py
alpine_native.py
macos.py
windows.py
```

They all share a set of base arguments. Individual scripts then add OS-specific arguments.

These scripts are not called by the build system, they have to be called manually after the build process completes. This is necessary because the SBOM scripts require access to Meson's `depmf.json` dependency manifest file, which is generated during `meson install`.

One exception is `save_args.py`, which is a helper script called by Meson (if enabled by `-Dgenerate_sbom_data=true`) which provides additional info about the build environment to the SBOM scripts.

Code in this directory is linted with [ruff](ruff), formatted with [black --preview](black) and type checked with [mypy](mypy). Lint rules for ruff are included in [`pyproject.toml`](pyproject.toml).

All subdirectories/packages in this directory are meant to be OS-independent. All OS-dependent functionality is usually contained in the entrypoint scripts themselves.

Each subdirectory/package includes a README describing the purpose of it.

[ruff]: https://docs.astral.sh/ruff/
[black]: https://black.readthedocs.io/
[mypy]: https://mypy-lang.org/
