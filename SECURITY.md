# Security Policy

This project is a recovery/stability kit for unsupported Linux-on-Apple hardware. Treat it as experimental system configuration, not a security product.

## Never Publish

Do not commit or paste:

- SSH private keys
- LUKS headers
- LUKS keyfiles
- Full raw `/boot/limine.conf` from a private machine
- Serial numbers
- Local IP addresses or hostnames
- Passwords, tokens, API keys, or browser/session exports

## Secure Defaults

The public installer does not enable these by default:

- SSH
- SDDM autologin
- Lid/idle overrides for remote maintenance
- Mobile lid hibernate
- LUKS auto-unlock preservation
- Limine path-hash stripping

They are available as explicit recovery flags because the original repair required delegated remote maintenance:

```bash
sudo ./install.sh --user "$USER" --enable-autologin --enable-ssh --enable-remote-maintenance
```

LUKS auto-unlock preservation has a separate opt-in:

```bash
sudo ./install.sh --user "$USER" --preserve-luks-auto-unlock
sudo OMARCHY_PRESERVE_LUKS_AUTO_UNLOCK=1 /usr/local/sbin/macbook-t1-omarchy-maintain manual
```

Mobile lid hibernate has a separate opt-in. Prefer this for carried laptops; do
not combine transport use with remote-maintenance lid/idle overrides.

```bash
sudo ./install.sh --user "$USER" --enable-lid-hibernate
```

Limine path-hash stripping is also recovery-only:

```bash
sudo LIMINE_STRIP_PATH_HASHES=1 /usr/local/sbin/macbook-t1-limine-unattended-fix
```

## Pre-Publish Checklist

Run these before publishing a release or pushing generated files:

```bash
git diff --check
git grep -nE 'PRIVATE KEY|BEGIN OPENSSH|github_pat_|gh[opsu]_|Authorization:|Bearer '
git grep -nE '192\.168\.|10\.[0-9]{1,3}\.|172\.(1[6-9]|2[0-9]|3[0-1])\.'
git grep -nE 'luks-header|/Users/|/home/[^/[:space:]]+|private-key-name'
```

Expected result: only intentional documentation warnings should match.

## Reporting

Open a GitHub issue for non-sensitive security concerns.

For sensitive reports, do not include private machine configs or secret material. Describe the issue in general terms and offer to share redacted details.
