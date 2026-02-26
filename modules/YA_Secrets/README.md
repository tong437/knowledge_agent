## YA Secrets Manager (SOPS + Age)

This repository stores encrypted secrets for YA Repos.

> Please run the scripts under the repository root directory, and ensure that the `path-to-module` in the commands below is replaced with the actual path to the module scripts.

### Setup Environment

- for Linux / MacOS:

```bash
chmod +x ./path-to-module/linux-macos.setup.sh
source ./path-to-module/linux-macos.setup.sh
```

- for Windows (PowerShell):

```powershell
.\path-to-module\windows.setup.ps1
```

### Generate age Key

To generate a new age key pair, run the following command:

- for Linux / MacOS:

```bash
chmod +x ./path-to-module/linux-macos.generate-age-key.sh
source ./path-to-module/linux-macos.generate-age-key.sh
```

- for Windows (PowerShell):

```powershell
.\path-to-module\windows.generate-age-key.ps1
```

### Copy Age Public Key

Copy the generated age public key to your clipboard. You will need to add this public key to the `.sops.yaml` file in this repository to allow encryption and decryption of secrets.

```yaml
creation_rules:
  - age: >-
      age13r4554wpmkkmh6lk2ky9d68nj7ctfgqv9d4f4ndu66h9usnxjfwsdcqvr7,
      your_generated_public_key_here
```

> The public key `age13r4554wpmkkmh6lk2ky9d68nj7ctfgqv9d4f4ndu66h9usnxjfwsdcqvr7` is the public key of the repository administrator and should remain unchanged.

### Move `.sops.yaml` to Repository Root

Move the `.sops.yaml` file to the root directory of this repository to enable SOPS to use the specified age keys for encryption and decryption.

### Manage Secrets

To manage secrets for a specific server, use the provided scripts:

- for Linux / MacOS:

```bash
chmod +x ./path-to-module/linux-macos.manage.sh
source ./path-to-module/linux-macos.manage.sh
```

- for Windows (PowerShell):

```powershell
.\path-to-module\windows.manage.ps1
```

This will open the secrets file in your default text editor. The default template for the secrets file is as follows:

```yaml
secrets:
  api_key: value
  database_password: value
```

Make sure to save the file after editing. When you close the editor, the script will automatically encrypt and save the secrets file to `env.yaml`.
When you need to update the secrets, simply run the management script again, and it will decrypt the existing secrets file for editing.
