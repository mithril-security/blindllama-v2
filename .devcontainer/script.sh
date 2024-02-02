#!/usr/bin/env bash

set -euxo pipefail

# Fix to solve the following az cli error
# ```sh
# $ az login                                           
# Traceback (most recent call last):
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/core/_session.py", line 37, in load
#     with open(self.filename, 'r', encoding=self._encoding) as f:
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# FileNotFoundError: [Errno 2] No such file or directory: '/home/vscode/.azure/azureProfile.json'

# During handling of the above exception, another exception occurred:

# Traceback (most recent call last):
#   File "<frozen runpy>", line 198, in _run_module_as_main
#   File "<frozen runpy>", line 88, in _run_code
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/__main__.py", line 39, in <module>
#     az_cli = get_default_cli()
#              ^^^^^^^^^^^^^^^^^
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/core/__init__.py", line 924, in get_default_cli
#     return AzCli(cli_name='az',
#            ^^^^^^^^^^^^^^^^^^^^
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/core/__init__.py", line 79, in __init__
#     ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/core/_session.py", line 50, in load
#     self.save()
#   File "/usr/local/pipx/venvs/azure-cli/lib/python3.11/site-packages/azure/cli/core/_session.py", line 54, in save
#     with open(self.filename, 'w', encoding=self._encoding) as f:
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# PermissionError: [Errno 13] Permission denied: '/home/vscode/.azure/azureProfile.json'
# ```

sudo chmod  777 $HOME/.azure 

# Patch to enable the environment to load properly in zsh vscode terminal
echo '[ -z "${POETRY_ACTIVE}" ] || source $(poetry env info --path)/bin/activate' >> ~/.zshrc

pipx install --editable mithril-os/render_template/

# Enable use of the TPM on your machine
sudo apt-get update
sudo apt-get install -y tpm2-tools swtpm-tools
# Install qemu
sudo apt-get install --no-install-recommends -y qemu-kvm ovmf qemu-utils
# sudo chown vscode /dev/kvm
sudo apt-get install --no-install-recommends -y pesign

# Install tools needed to unpack an initrd image
sudo apt install --no-install-recommends -y cpio zstd

# Install Earthly
sudo /bin/sh -c 'wget https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -O /usr/local/bin/earthly && chmod +x /usr/local/bin/earthly && /usr/local/bin/earthly bootstrap --with-autocomplete'

# Install azcopy
sudo bash -c 'cd /usr/local/bin; curl -L https://aka.ms/downloadazcopy-v10-linux | tar --strip-components=1 --exclude=*.txt -xzvf -; chmod +x azcopy'

# Add /go/bin to $PATH
echo 'export PATH=/go/bin:$HOME/bin:/usr/local/bin:$PATH' >> ~/.zshrc

# Install crane
go install github.com/google/go-containerregistry/cmd/crane@latest

# Install slsa-verifier
go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.4.1

