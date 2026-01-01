import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_ed25519_keypair():
    """
    #!/bin/sh
    set -e

    KEY_NAME="badge_ed25519_tmp"

    ssh-keygen -t ed25519 -f "$KEY_NAME" -N "" -q

    PUBLIC_KEY_B64=$(
      ssh-keygen -yf "$KEY_NAME" \
      | awk '{print $2}' \
      | base64 -d \
      | tail -c 32 \
      | base64
    )

    PRIVATE_KEY_B64=$(
      openssl pkey -in "$KEY_NAME" -outform DER 2>/dev/null \
      | tail -c 32 \
      | base64
    )

    rm -f "$KEY_NAME" "$KEY_NAME.pub"

    echo "PUBLIC_KEY_B64=$PUBLIC_KEY_B64"
    echo "PRIVATE_KEY_B64=$PRIVATE_KEY_B64"

    :return:
    """
    private_key = ed25519.Ed25519PrivateKey.generate()

    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return (
        base64.b64encode(public_raw).decode(),
        base64.b64encode(private_raw).decode(),
    )


def sign_ed25519(private_key_b64: str, message: str) -> str:
    key = ed25519.Ed25519PrivateKey.from_private_bytes(
        base64.b64decode(private_key_b64)
    )
    return base64.b64encode(key.sign(message.encode())).decode()
