package compliance.cryptographic

default allow = false

banned_algorithms := {"MD5", "SHA1", "DES", "3DES", "RC4"}

allow {
    not input.algorithm in banned_algorithms
}

violation[msg] {
    input.algorithm in banned_algorithms
    msg := sprintf("Non-FIPS algorithm detected: %s. Use SHA-256 or AES-256-GCM instead.", [input.algorithm])
}
