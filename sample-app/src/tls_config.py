import ssl
import requests


def legacy_tls_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def weak_minimum_tls_version():
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_1
    return context


def fetch_internal_service():
    return requests.get("https://internal.example.local/health", verify=False, timeout=5)
