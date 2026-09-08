# Troubleshooting

## Boot Hangs At OS Selection

Use the console or rescue entry, then run:

```bash
sudo /usr/local/sbin/macbook-t1-limine-unattended-fix
sudo reboot
```

Check `/boot/limine.conf`:

```bash
grep -E '^(timeout|default_entry):' /boot/limine.conf
```

Expected:

```text
timeout: 1
default_entry: 1
```

If Limine reports a BLAKE2 hash mismatch for a boot entry, first confirm that you have a recovery path and understand the Secure Boot implications. Then strip path hashes once:

```bash
sudo LIMINE_STRIP_PATH_HASHES=1 /usr/local/sbin/macbook-t1-limine-unattended-fix
```

## Black Screen After Login

Confirm the Radeon symlink exists:

```bash
ls -l /dev/dri/intel-igpu /dev/dri/radeon-dgpu
```

Confirm the Hyprland block exists:

```bash
grep -n 'MacBookPro13,3 T1 graphics' ~/.config/hypr/hyprland.lua
grep -n 'AQ_NO_MODIFIERS' ~/.config/hypr/hyprland.lua
```

Check for GPU reset errors:

```bash
sudo journalctl -b -k | grep -Ei 'amdgpu|ring|sdma|REG_WAIT|gpu reset|drm'
```

Reapply the maintenance script:

```bash
sudo OMARCHY_USER="$USER" /usr/local/sbin/macbook-t1-omarchy-maintain repair
sudo reboot
```

## SDDM Does Not Autologin

Check:

```bash
cat /etc/sddm.conf.d/autologin.conf
ls /usr/local/share/wayland-sessions/omarchy.desktop
systemctl status sddm
```

Reinstall with autologin:

```bash
sudo ./install.sh --user "$USER" --enable-autologin
```

## Touch Bar Missing

Check DKMS:

```bash
dkms status
systemctl status t1-touchbar.service
```

This repo does not vendor the Touch Bar driver. It only preserves and enables the service if it is already installed.

## iPhone Hotspot Or 5 GHz Wi-Fi Missing

Check whether the Broadcom BCM43602 card exposes a 5 GHz band:

```bash
iw list | grep -E 'Band [12]:|\\* 5[0-9]{3}\\.0 MHz'
sudo dmesg | grep -Ei 'brcmfmac|clm_blob|txcap_blob'
```

If only 2.4 GHz is visible, install the optional NVRAM override from a locally supplied source file:

```bash
sudo ./install.sh --user "$USER" \
  --enable-bcm43602-5ghz-wifi \
  --bcm43602-nvram-file /path/to/brcmfmac43602-pcie.txt
sudo reboot
```

After reboot, scan for the hotspot:

```bash
sudo nmcli dev wifi rescan
nmcli device wifi list | grep -i iphone
```

## Audio Missing

See [audio.md](audio.md).

## After Package Updates

The pacman hook and Omarchy post-update hook should run automatically. To force a repair:

```bash
sudo OMARCHY_USER="$USER" /usr/local/sbin/macbook-t1-omarchy-maintain manual
```

Logs:

```bash
sudo tail -200 /var/log/macbook-t1-omarchy-maintain.log
tail -200 ~/.local/state/macbook-t1-omarchy/macbook-t1-omarchy-post-update.log
```
