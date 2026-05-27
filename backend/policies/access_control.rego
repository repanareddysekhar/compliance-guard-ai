package compliance.access_control

default allow = false

allow {
    input.auth_enabled == true
    input.cors_wildcard == false
}

violation[msg] {
    input.auth_enabled == false
    msg := "Authentication is not enabled for this service."
}

violation[msg] {
    input.cors_wildcard == true
    msg := "Wildcard CORS policy detected. Restrict origins for better security."
}
