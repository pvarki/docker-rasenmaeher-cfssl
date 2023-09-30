{{ $default_expiry := getenv "CFSSL_SIGN_DEFAULT_EXPIRY" "1008h" }}
{
  "signing": {
    "default": {
      "expiry": "{{ print $default_expiry }}"
    },
    "profiles": {
      "client": {
        "expiry": "{{ getenv "CFSSL_SIGN_CLIENT_EXPIRY" $default_expiry }}",
        "usages": [
          "signing",
          "digital signature",
          "key encipherment",
          "client auth"
        ]
      },
      "intermediate_ca": {
        "ca_constraint": {
          "is_ca": true,
          "max_path_len": 0,
          "max_path_len_zero": true
        },
        "expiry": "{{ getenv "CFSSL_SIGN_CA_EXPIRY" "2016h" }}",
        "usages": [
          "signing",
          "digital signature",
          "key encipherment",
          "cert sign",
          "crl sign",
          "server auth",
          "client auth"
        ]
      },
      "peer": {
        "expiry": "{{ getenv "CFSSL_SIGN_PEER_EXPIRY" $default_expiry }}",
        "usages": [
          "signing",
          "digital signature",
          "key encipherment",
          "client auth",
          "server auth"
        ]
      },
      "server": {
        "expiry": "{{ getenv "CFSSL_SIGN_SERVER_EXPIRY" $default_expiry }}",
        "usages": [
          "signing",
          "digital signing",
          "key encipherment",
          "server auth"
        ]
      }
    }
  }
}
