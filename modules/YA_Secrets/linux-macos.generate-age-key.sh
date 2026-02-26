#!/usr/bin/env bash
set -e

KEY_DIR="$HOME/.config/sops/keys"
KEY_FILE="$KEY_DIR/age.key"

mkdir -p "$KEY_DIR"

if [ -f "$KEY_FILE" ]; then
    echo "Age key already exists: $KEY_FILE"
else
    echo "Generating Age key..."
    age-keygen -o "$KEY_FILE"
fi

echo
echo "=== Public key ==="
age-keygen -y "$KEY_FILE"
echo
echo "Private key saved at $KEY_FILE"
echo "Keep it safe! Do not share."

# -----------------------------
# 自动配置环境变量
# -----------------------------
export SOPS_AGE_KEY_FILE="$KEY_FILE"

SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "export SOPS_AGE_KEY_FILE=" "$SHELL_RC"; then
        echo "export SOPS_AGE_KEY_FILE=\"$KEY_FILE\"" >> "$SHELL_RC"
        echo "Added SOPS_AGE_KEY_FILE to $SHELL_RC"
        echo "Please restart your terminal or run 'source $SHELL_RC' to apply the change."
    fi
else
    echo "Cannot detect shell config file to persist SOPS_AGE_KEY_FILE. It is set for this session only."
fi

echo
echo "Environment variable SOPS_AGE_KEY_FILE is set to $KEY_FILE for this session."