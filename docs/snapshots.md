# Snapshot Practice

The original recovery process kept three meaningful snapshots:

- Previous stable graphics baseline, before audio was fixed.
- Current stable state with graphics, Touch Bar, and audio working.
- Current stable state plus update-survival hooks.

Recommended flow:

```bash
sudo snapper create --description "before MacBookPro13,3 T1 Omarchy change"
sudo ./install.sh --user "$USER"
sudo reboot
```

After verifying the desktop, Touch Bar, and audio:

```bash
sudo snapper create --description "MacBookPro13,3 T1 Omarchy stable"
```

List snapshots:

```bash
sudo snapper list
```

Clean up old snapshots only after confirming a known-good boot:

```bash
sudo snapper delete SNAPSHOT_NUMBER
```

Remember that Snapper usually protects the root Btrfs subvolume. On many Omarchy installs, `/boot` is a separate EFI system partition and is not covered by Snapper. Keep separate backups of `/boot/limine.conf` before heavy bootloader work.
