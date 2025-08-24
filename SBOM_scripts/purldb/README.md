Modules interacting with 'purldb'.

purldb is a dict whose keys are `keys.PurlNames` enum members and whose values are strings used in `purl` and `bom-ref` keys of CycloneDX components.

The keys used are internal and do not have to hold any meaning, they are only used in the purldb mapping. But they are sometimes used at the base for the resulting purl.

purldb ensures that when a specific purl is referenced multiple times (each purl is referenced at least twice, once in its component and once in the dependencies array of the resulting SBOM), no purl mismatch will occur.

`keys.PurlNames` is a static enum containing all purls used by all entrypoint scripts. Because of its nature, this class contains a summary of all possible dependencies of android-tools-static, which makes it a useful resource.
