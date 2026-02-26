#!/usr/bin/env bash
set -e

SOPS_VERSION="3.11.0"

echo "=== Installing age + sops ==="

OS=$(uname)
ARCH=$(uname -m)

if [[ "$ARCH" == "x86_64" ]]; then
    ARCH_STR="amd64"
elif [[ "$ARCH" == "aarch64" ]]; then
    ARCH_STR="arm64"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

if [[ "$OS" == "Linux" ]]; then
    echo "Linux detected..."
    if command -v age >/dev/null 2>&1; then
        echo "age already installed"
    else
        echo "Installing age..."
        sudo apt update || true
        sudo apt install -y age || true
    fi

    echo "Downloading sops..."
    curl -LO "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.${ARCH_STR}"
    sudo mv "sops-v${SOPS_VERSION}.linux.${ARCH_STR}" /usr/local/bin/sops
    sudo chmod +x /usr/local/bin/sops
fi

if [[ "$OS" == "Darwin" ]]; then
    echo "macOS detected..."
    if ! command -v age >/dev/null 2>&1; then
        if command -v brew >/dev/null 2>&1; then
            brew install age
        elif command -v port >/dev/null 2>&1; then
            sudo port install age
        else
            echo "Homebrew or MacPorts required for macOS. Please install one of them."
            exit 1
        fi
    fi

    echo "Downloading sops..."
    curl -LO "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.darwin.${ARCH_STR}"
    sudo mv "sops-v${SOPS_VERSION}.darwin.${ARCH_STR}" /usr/local/bin/sops
    sudo chmod +x /usr/local/bin/sops
fi

if ! command -v age >/dev/null; then
    echo "age installation failed!"
    exit 1
fi
if ! command -v sops >/dev/null; then
    echo "sops installation failed!"
    exit 1
fi

echo "=== Done. age + sops installed ==="
age --version
sops --version