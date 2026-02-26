#!/bin/bash

if [ ! -f ".sops.yaml" ]; then
    echo "No sops config file found (.sops.yaml)."
    echo "Please copy the config file from submodule before running this script."
    exit 1
fi

FILE="env.yaml"
FILE_EXISTS=false

if [ -f "$FILE" ]; then
    FILE_EXISTS=true
else
    # create template if file not exist
    cat > "$FILE" <<EOF
# Add your secrets here
secret_key: value
database_password: value
EOF
    echo "Created $FILE"
fi

# create temp file
TEMP=$(mktemp)
TEMP_YAML="${TEMP}.yaml"
mv "$TEMP" "$TEMP_YAML"
TEMP="$TEMP_YAML"

# if file exists, decrypt with sops
if [ "$FILE_EXISTS" = true ]; then
    sops -d --output "$TEMP" "$FILE"
else
    cp "$FILE" "$TEMP"
fi

# open editor
if command -v code >/dev/null 2>&1; then
    code --wait "$TEMP"
else
    ${EDITOR:-nano} "$TEMP"
fi

# encrypt back with sops and overwrite original
sops -e -i "$TEMP"
mv -f "$TEMP" "$FILE"

echo "Saved and encrypted $FILE"
