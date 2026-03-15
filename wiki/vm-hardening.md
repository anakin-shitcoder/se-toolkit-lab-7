# VM hardening

<h2>Table of contents</h2>

- [What is VM hardening](#what-is-vm-hardening)
- [Set up login as the non-root user `<user>`](#set-up-login-as-the-non-root-user-user)
  - [Connect to your VM as the user `root` (LOCAL)](#connect-to-your-vm-as-the-user-root-local)
  - [Create the non-root user `<user>` (REMOTE)](#create-the-non-root-user-user-remote)
  - [Set up the `SSH` key authentication for the user `<user>` (REMOTE)](#set-up-the-ssh-key-authentication-for-the-user-user-remote)
  - [Connect to your VM by `SSH` as the user `<user>` (LOCAL)](#connect-to-your-vm-by-ssh-as-the-user-user-local)
  - [Harden the `SSH` config (REMOTE)](#harden-the-ssh-config-remote)
  - [Update the local `SSH` config (LOCAL)](#update-the-local-ssh-config-local)
  - [Restart `sshd` (REMOTE)](#restart-sshd-remote)
- [Set up additional protection](#set-up-additional-protection)
  - [Set up `ufw` firewall (REMOTE)](#set-up-ufw-firewall-remote)
  - [Set up `fail2ban` (REMOTE)](#set-up-fail2ban-remote)

## What is VM hardening

VM hardening is the process of securing a [virtual machine](./vm.md#what-is-a-vm) by reducing its attack surface.

Docs:

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)

Steps:

1. [Set up login as the non-root user `<user>`](#set-up-login-as-the-non-root-user-user)
2. [Set up additional protection](#set-up-additional-protection)

## Set up login as the non-root user `<user>`

> [!NOTE]
> Replace [`<user>`](./operating-system.md#user-placeholder) with the actual [username](./operating-system.md#username).

Complete these steps:

<!-- no toc -->
1. [Connect to your VM as the user `root` (LOCAL)](#connect-to-your-vm-as-the-user-root-local)
2. [Create the non-root user `<user>` (REMOTE)](#create-the-non-root-user-user-remote)
3. [Set up the `SSH` key authentication for the user `<user>` (REMOTE)](#set-up-the-ssh-key-authentication-for-the-user-user-remote)
4. [Connect to your VM by `SSH` as the user `<user>` (LOCAL)](#connect-to-your-vm-by-ssh-as-the-user-user-local)
5. [Harden the `SSH` config (REMOTE)](#harden-the-ssh-config-remote)
6. [Update the local `SSH` config (LOCAL)](#update-the-local-ssh-config-local)
7. [Restart `sshd` (REMOTE)](#restart-sshd-remote)

### Connect to your VM as the user `root` (LOCAL)

1. To connect to your VM as [the user `root`](./linux.md#the-root-user),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   ssh root@<your-vm-ip-address>
   ```

   Replace [`<your-vm-ip-address>`](./vm.md#your-vm-ip-address).

### Create the non-root user `<user>` (REMOTE)

> [!NOTE]
> Replace [`<user>`](./operating-system.md#user-placeholder) with the actual [username](./operating-system.md#username).

1. To create a new user `<user>`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   adduser <user>
   ```

2. To add the user `<user>` to the [`sudo` group](./linux.md#sudo-group),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   usermod -aG sudo <user>
   ```

### Set up the `SSH` key authentication for the user `<user>` (REMOTE)

> [!NOTE]
> Replace [`<user>`](./operating-system.md#user-placeholder) with the actual [username](./operating-system.md#username).

1. To create the `.ssh` directory for the user `<user>`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   mkdir -p /home/<user>/.ssh
   ```

2. To copy the authorized keys from the user `root`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp /root/.ssh/authorized_keys /home/<user>/.ssh/
   ```

3. To set the correct ownership on the `.ssh` directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   chown -R <user>:<user> /home/<user>/.ssh
   ```

   **Note:** See [Change the owner and group (recursive)](./linux-administration.md#change-the-owner-and-group-recursive).

4. To set the correct permissions on the `.ssh` directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   chmod 700 /home/<user>/.ssh
   ```

   **Note:** See [Set the permissions](./linux-administration.md#set-the-permissions).

   <!-- TODO why these permissions are correct? -->

5. To set the correct permissions on the `authorized_keys` file,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   chmod 600 /home/<user>/.ssh/authorized_keys
   ```

   <!-- TODO why these permissions are correct? -->

### Connect to your VM by `SSH` as the user `<user>` (LOCAL)

> [!NOTE]
> Replace [`<user>`](./operating-system.md#user-placeholder) with the actual [username](./operating-system.md#username).

1. [Open a new `VS Code Terminal`](./vs-code.md#open-a-new-vs-code-terminal).

2. To connect as the user `<user>`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   ssh -i ~/.ssh/se_toolkit_key <user>@<your-vm-ip-address>
   ```

   Replace the placeholders:

   - [`<user>`](./operating-system.md#user-placeholder)
   - [`<your-vm-ip-address>`](./vm.md#your-vm-ip-address)

3. Confirm the connection did not prompt for a password.

### Harden the `SSH` config (REMOTE)

<!-- TODO check there's this file at all with this content -->

1. [Connect to your VM as the user `<user>`](#connect-to-your-vm-by-ssh-as-the-user-user-local) if not yet connected.

2. To open the [`SSH`](./ssh.md#what-is-ssh) config,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo nano /etc/ssh/sshd_config
   ```

3. Find the line `PermitRootLogin` and set it to:

   ```text
   PermitRootLogin no
   ```

4. Find the line `PasswordAuthentication` and set it to:

   ```text
   PasswordAuthentication no
   ```

5. Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

### Update the local `SSH` config (LOCAL)

> [!NOTE]
> Replace [`<user>`](./operating-system.md#user-placeholder) with the actual [username](./operating-system.md#username).

1. [Open the file](./vs-code.md#open-the-file):
   `~/.ssh/config`

2. Find the `se-toolkit-vm` entry and change `User root` to `User <user>`.

   Replace the placeholder [`<user>`](./operating-system.md#user-placeholder).

   The result should look like this:

   - `Linux`, `Windows`:

     ```text
     Host se-toolkit-vm
        HostName <your-vm-ip-address>
        User <user>
        IdentityFile ~/.ssh/se_toolkit_key
        AddKeysToAgent yes
     ```

   - `macOS`:

     ```text
     Host se-toolkit-vm
        HostName <your-vm-ip-address>
        User <user>
        IdentityFile ~/.ssh/se_toolkit_key
        AddKeysToAgent yes
        UseKeychain yes
     ```

### Restart `sshd` (REMOTE)

1. To validate the config,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo sshd -t
   ```

   If the command prints no output, the config is valid. If it prints errors, fix them in `/etc/ssh/sshd_config` before continuing.

2. To restart the service,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo systemctl restart sshd
   ```

3. To verify you can still connect,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   ssh se-toolkit-vm
   ```

4. Confirm you are logged in as `<user>`, not `root`.

> [!IMPORTANT]
> Keep your current `SSH` session open until you confirm the new connection works. If the new connection fails, use the existing session to fix the config.

## Set up additional protection

Complete these steps:

<!-- no toc -->
1. [Set up `ufw` firewall (REMOTE)](#set-up-ufw-firewall-remote)
2. [Set up `fail2ban` (REMOTE)](#set-up-fail2ban-remote)

### Set up `ufw` firewall (REMOTE)

`ufw` (`Uncomplicated Firewall`) is a simple firewall for [`Linux`](./linux.md#what-is-linux). By default, `ufw` denies all incoming traffic. The steps below create exceptions for the ports your VM needs.

1. To allow [`SSH`](./ssh.md#what-is-ssh),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo ufw allow 22
   ```

   > 🟪 **Important**
   > Always allow `SSH` (port 22) before enabling `ufw`.
   > Otherwise, you will lock yourself out of your VM.

2. Find the [`<caddy-port>`](./caddy.md#caddy-port).

3. To allow the application port,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo ufw allow <caddy-port>
   ```

4. To enable the firewall,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo ufw enable
   ```

5. To check the status,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo ufw status
   ```

### Set up `fail2ban` (REMOTE)

`fail2ban` blocks IP addresses that make too many failed login attempts. Even after password authentication is disabled, `fail2ban` remains useful: it rate-limits repeated [`SSH`](./ssh.md#what-is-ssh) connection attempts and can be extended to protect other services.

1. To update the package list,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo apt update
   ```

2. To install `fail2ban`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo apt install -y fail2ban
   ```

3. To enable the service,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo systemctl enable fail2ban
   ```

4. To start the service,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo systemctl start fail2ban
   ```

5. To check the status,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   sudo systemctl status fail2ban
   ```
