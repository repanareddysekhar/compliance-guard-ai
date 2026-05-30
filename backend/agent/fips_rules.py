"""FIPS 140-3 cryptographic compliance rules used by check_crypto and OPA."""

BANNED_ALGORITHMS = ["MD5", "SHA1", "DES", "3DES", "RC4"]
FIPS_APPROVED = ["SHA-256", "SHA-384", "SHA-512", "AES-256", "RSA-2048+", "ECDSA-P256+"]

BANNED_CRYPTO = {
    "md5": {
        "finding": "MD5",
        "description": "Non-FIPS algorithm MD5 detected.",
        "remediation": "Replace MD5 with SHA-256 or SHA-512 for hashing operations.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bhashlib\.md5\s*\(",
            r"\bmd5\s*\(",
            r"\bcreateHash\s*\(\s*['\"]md5['\"]",
            r"\bMessageDigest\.getInstance\s*\(\s*['\"]MD5['\"]",
            r"\bCryptoJS\.MD5\s*\(",
            r"\bMD5\.Create\s*\(",
        ],
    },
    "sha1": {
        "finding": "SHA1",
        "description": "Non-FIPS algorithm SHA1 detected.",
        "remediation": "Replace SHA1 with SHA-256 or stronger approved hashing.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bhashlib\.sha1\s*\(",
            r"\bsha1\s*\(",
            r"\bcreateHash\s*\(\s*['\"]sha1['\"]",
            r"\bMessageDigest\.getInstance\s*\(\s*['\"]SHA-?1['\"]",
            r"\bCryptoJS\.SHA1\s*\(",
            r"\bSHA1\.Create\s*\(",
        ],
    },
    "des": {
        "finding": "DES",
        "description": "Weak DES encryption detected.",
        "remediation": "Use AES-256-GCM for symmetric encryption.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bcreateCipher(?:iv)?\s*\(\s*['\"]des(?:-|['\"])",
            r"\bCipher\.getInstance\s*\(\s*['\"]DES(?:/|['\"])",
            r"\bDES\.Create\s*\(",
            r"\bCryptoJS\.DES\.",
            r"\balgorithms\.DES\b",
        ],
    },
    "rc4": {
        "finding": "RC4",
        "description": "Weak RC4 cipher detected.",
        "remediation": "Use AES-256-GCM or ChaCha20-Poly1305 instead.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bARC4\.new\s*\(",
            r"\bcreateCipher(?:iv)?\s*\(\s*['\"]rc4['\"]",
            r"\bCipher\.getInstance\s*\(\s*['\"]RC4['\"]",
            r"\bCryptoJS\.RC4\.",
        ],
    },
    "tls10": {
        "finding": "TLSv1.0",
        "description": "Deprecated TLS 1.0 protocol detected.",
        "remediation": "Disable TLS 1.0 and require TLS 1.2 or TLS 1.3 with approved cipher suites.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bssl\.PROTOCOL_TLSv1\b",
            r"\bTLSVersion\.TLSv1\b",
            r"\bminimum_version\s*=\s*ssl\.TLSVersion\.TLSv1\b",
            r"\bsecureProtocol\s*:\s*['\"]TLSv1_method['\"]",
        ],
    },
    "tls11": {
        "finding": "TLSv1.1",
        "description": "Deprecated TLS 1.1 protocol detected.",
        "remediation": "Disable TLS 1.1 and require TLS 1.2 or TLS 1.3 with approved cipher suites.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bssl\.PROTOCOL_TLSv1_1\b",
            r"\bTLSVersion\.TLSv1_1\b",
            r"\bminimum_version\s*=\s*ssl\.TLSVersion\.TLSv1_1\b",
            r"\bsecureProtocol\s*:\s*['\"]TLSv1_1_method['\"]",
        ],
    },
    "disabled_cert_validation": {
        "finding": "disabled_cert_validation",
        "description": "TLS certificate validation is disabled.",
        "remediation": "Enable certificate validation, require hostname verification, and trust only approved CA bundles.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bverify\s*=\s*False\b",
            r"\bcheck_hostname\s*=\s*False\b",
            r"\bCERT_NONE\b",
            r"\brejectUnauthorized\s*:\s*false\b",
            r"\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?",
        ],
    },
}

CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".java", ".js", ".jsx", ".kt", ".mjs", ".php",
    ".py", ".rb", ".rs", ".scala", ".swift", ".ts", ".tsx",
}
