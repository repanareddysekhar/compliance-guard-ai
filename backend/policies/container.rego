package compliance.container

default allow = false

allow {
    input.user != "root"
    input.has_healthcheck == true
    input.tag != "latest"
}

violation[msg] {
    input.user == "root"
    msg := "Container running as root. Use a non-root user (USER appuser)."
}

violation[msg] {
    input.tag == "latest"
    msg := "Using 'latest' Docker tag. Pin to a specific version for reproducibility."
}

violation[msg] {
    not input.has_healthcheck
    msg := "No HEALTHCHECK instruction found in Dockerfile."
}
