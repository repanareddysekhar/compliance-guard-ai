package compliance.dependency

default allow = false

allow {
    count(input.vulnerabilities) == 0
}

violation[msg] {
    some v in input.vulnerabilities
    v.severity == "critical"
    msg := sprintf("Critical vulnerability found in %s: %s", [input.package_name, v.id])
}

violation[msg] {
    some v in input.vulnerabilities
    v.severity == "high"
    msg := sprintf("High vulnerability found in %s: %s", [input.package_name, v.id])
}
