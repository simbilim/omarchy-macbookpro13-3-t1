# Security Notes

This setup was built for recovery and delegated remote maintenance first. Some choices trade security for reliability and unattended access.

## SDDM Autologin

The default installer does not enable SDDM autologin.

Disable it:

```bash
sudo ./install.sh --user "$USER"
sudo systemctl restart sddm
```

Enable it only for unattended repair:

```bash
sudo ./install.sh --user "$USER" --enable-autologin
```

## LUKS Auto-Unlock

This repo does not create a LUKS keyfile, add a new LUKS keyslot, or preserve LUKS auto-unlock by default.

If `/crypto_keyfile.bin` already exists, the maintenance script can preserve the matching `mkinitcpio` config so the existing auto-unlock setup survives updates. Make that behavior persistent with the installer flag:

```bash
sudo ./install.sh --user "$USER" --preserve-luks-auto-unlock
```

For a one-shot maintenance run only:

```bash
sudo OMARCHY_PRESERVE_LUKS_AUTO_UNLOCK=1 /usr/local/sbin/macbook-t1-omarchy-maintain manual
```

Treat this as insecure for normal laptop use. A keyfile embedded into the UKI can make disk encryption ineffective against anyone with physical access to the laptop and boot partition.

Do not commit any of these files to GitHub:

- `/crypto_keyfile.bin`
- LUKS header backups
- SSH private keys
- Raw `/boot/limine.conf` copied from a private machine
- Any file containing local IP addresses, hostnames, or account names

To remove an existing auto-unlock setup, identify the extra LUKS keyslot first:

```bash
sudo cryptsetup luksDump /dev/YOUR_LUKS_DEVICE
```

Then remove the keyslot, remove the keyfile and mkinitcpio drop-in, rebuild the UKI, and reboot:

```bash
sudo cryptsetup luksKillSlot /dev/YOUR_LUKS_DEVICE SLOT_NUMBER
sudo rm -f /crypto_keyfile.bin /etc/mkinitcpio.conf.d/zz-macbook-t1-luks-keyfile.conf
sudo limine-mkinitcpio
sudo /usr/local/sbin/macbook-t1-limine-unattended-fix
sudo reboot
```

Replace `YOUR_LUKS_DEVICE` and `SLOT_NUMBER` with values from your own machine.

## SSH, Remote Maintenance, And Lid Behavior

The default installer does not enable SSH and does not change lid/idle behavior.

For delegated recovery sessions only:

```bash
sudo ./install.sh --user "$USER" --enable-ssh --enable-remote-maintenance
```

Use key-only SSH, disable password authentication if possible, and turn these settings off after recovery if you do not need them.

Remote-maintenance lid/idle overrides are unsafe for transport: they can keep a closed laptop running in a bag. Hibernation also failed during the 9 September investigation, so the earlier recommendation to enable it has been withdrawn. See [the investigation](stability-2026-09-09.md) for the replacement profile and its validation status.

The installer rejects combining remote maintenance and lid hibernate, because systemd drop-in ordering would otherwise make the higher-priority remote-maintenance ignore rules win.

Installer choices are stored locally in `/etc/macbook-t1-omarchy.conf` so the update hooks can preserve deliberate opt-in settings. Review that file before enabling the machine for long-term use.

The maintenance script refuses to read that config if it is symlinked, not owned by root, or writable by group/other users. It parses only known keys and 0/1 boolean values; it does not source the file as shell code.

To turn off the managed recovery options:

```bash
sudo ./install.sh --user "$USER"
sudo systemctl disable --now sshd.service
sudo reboot
```

The installer removes the managed SDDM autologin file, managed remote-maintenance logind override, managed mobile lid-hibernate override, and managed LUKS keyfile mkinitcpio drop-ins when their opt-in flags are off. It then rebuilds the UKI. If the rebuild fails or the rebuild command is missing, the maintenance script exits with failure and keeps a pending marker at `/var/lib/macbook-t1-omarchy/pending-uki-rebuild` so the next run retries.

It does not remove `/crypto_keyfile.bin` or LUKS keyslots; remove those manually as described above.

Legacy cleanup only removes old generated artifacts whose contents match known MacBook T1 recovery files. Unknown content at those old fixed paths is preserved and logged as a warning.

## BCM43602 Wi-Fi NVRAM

The default installer does not install Broadcom NVRAM calibration files.

On the tested MacBookPro13,3, the stock `brcmfmac` path exposed only 2.4 GHz. The optional BCM43602 override lets the card advertise 5 GHz and see iPhone hotspots that are broadcast on 5 GHz:

```bash
sudo ./install.sh --user "$USER" \
  --enable-bcm43602-5ghz-wifi \
  --bcm43602-nvram-file /path/to/brcmfmac43602-pcie.txt
```

The NVRAM file is not included in this repository. It may be legally sensitive to redistribute, and it contains board-specific RF calibration data. The installer gates this option to `MacBookPro13,3` with PCI device `14e4:43ba`, snapshots the supplied file with a no-follow open, validates and sanitizes only that root-controlled snapshot, copies the sanitized source into `/usr/local/share/macbook-t1-omarchy/`, replaces `macaddr=` with a stable locally administered address, and installs the active files under `/usr/lib/firmware/updates/brcm/`.

The NetworkManager privacy workaround is scoped to the `wlp3s0` `brcmfmac` device. It disables scan MAC randomization and uses the permanent locally administered MAC only for that affected Broadcom interface. That address is stable across networks, so enabling this option can make this laptop easier to track on Wi-Fi networks than a fully randomized configuration.

To disable the managed Wi-Fi override:

```bash
sudo ./install.sh --user "$USER"
sudo reboot
```

Do not publish private firmware dumps, device-specific MAC addresses, or files copied from `/usr/lib/firmware/updates/brcm/` without reviewing redistribution rights and privacy impact.

## Boot Integrity

The Limine helper preserves boot file hashes by default. Removing hashes may bypass or break boot integrity checks depending on your Limine/Secure Boot setup.

Only strip Limine path hashes as a recovery action for a known broken boot config:

```bash
sudo LIMINE_STRIP_PATH_HASHES=1 /usr/local/sbin/macbook-t1-limine-unattended-fix
```
