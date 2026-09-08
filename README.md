# Omarchy on MacBookPro13,3 T1

Survival kit for running [Omarchy](https://omarchy.org/) on the 2016 15-inch MacBook Pro with Touch Bar.

This repo captures the configuration that made one MacBookPro13,3 usable with Omarchy: stable internal display, unattended boot defaults, optional SDDM autologin, working Touch Bar support when the T1 driver is installed, and working internal speaker audio through the CS8409 DKMS driver.

It is intentionally not a machine dump. It does not include SSH keys, LUKS headers, LUKS keyfiles, Snapper snapshot contents, hostnames, local IP addresses, or boot configs copied from a private machine.

## Tested Hardware

- Apple model identifier: `MacBookPro13,3`
- Marketing model: MacBook Pro 15-inch, 2016, Touch Bar
- Board: `Mac-A5C67F76ED83108C`
- CPU graphics: Intel Skylake-H HD Graphics 530, PCI ID `8086:191b`
- dGPU: AMD/ATI Baffin / Radeon Pro 450/455/460 family, PCI ID `1002:67ef`
- Audio controller: Intel 100/C230 HD Audio, PCI ID `8086:a170`
- HDMI/DP audio: AMD/ATI Baffin HDMI/DP Audio, PCI ID `1002:aae0`
- Tested Omarchy: `4.0.2`
- Tested kernel: `7.1.9-arch1-2`

Other T1-era MacBook Pro models may need changes. Do not assume this is correct for T2 Macs or Apple Silicon Macs.

## What This Installs

- Limine kernel flags that avoid Radeon power-management instability.
- Stable `/dev/dri/intel-igpu` and `/dev/dri/radeon-dgpu` symlinks.
- Hyprland/Aquamarine environment overrides:
  - `AQ_DRM_DEVICES=/dev/dri/radeon-dgpu`
  - `AQ_NO_MODIFIERS=1`
  - `HYPRLAND_EGL_NO_MODIFIERS=1`
- A systemd unit that keeps the Radeon dGPU out of D3cold.
- SDDM ordering so the display manager waits for the GPU setup.
- Optional SDDM autologin to the Omarchy session.
- Optional SSH enablement, remote-maintenance lid/idle behavior, and mobile lid hibernate.
- Optional Broadcom BCM43602 Apple NVRAM override so 5 GHz Wi-Fi and iPhone hotspots are visible.
- Limine unattended boot guard: short timeout and default Linux entry.
- Pacman and Omarchy post-update hooks that reapply these changes after updates.
- Optional audio installer for [davidjo/snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro).

## Quick Install

Run from an Omarchy shell on the MacBook:

```bash
git clone https://github.com/simbilim/omarchy-macbookpro13-3-t1.git
cd omarchy-macbookpro13-3-t1
sudo ./install.sh --user "$USER"
```

Then reboot:

```bash
sudo reboot
```

If the desktop reaches Hyprland and graphics are stable, install the CS8409 audio driver:

```bash
sudo ./install.sh --user "$USER" --install-audio-dkms
sudo reboot
```

If Wi-Fi only sees 2.4 GHz networks, enable the BCM43602 5 GHz override with a locally supplied Apple NVRAM text file:

```bash
sudo ./install.sh --user "$USER" \
  --enable-bcm43602-5ghz-wifi \
  --bcm43602-nvram-file /path/to/brcmfmac43602-pcie.txt
sudo reboot
```

This repository does not include the NVRAM file. The installer validates the hardware, stores the source file under root control, substitutes a stable local MAC address, and installs the active override under `/usr/lib/firmware/updates/brcm/`.

## Important Security Notes

This repo does not enable SSH, SDDM autologin, remote-maintenance lid/idle overrides, mobile lid hibernate, the BCM43602 5 GHz Wi-Fi override, or LUKS auto-unlock by default.

For unattended remote repair, opt in explicitly:

```bash
sudo ./install.sh --user "$USER" --enable-autologin --enable-ssh --enable-remote-maintenance
```

Do not use remote-maintenance lid/idle overrides while transporting the laptop. They can keep the machine running with the lid closed. For mobile use on this model, prefer hibernate-on-lid-close:

```bash
sudo ./install.sh --user "$USER" --enable-lid-hibernate
```

The installer rejects combining `--enable-remote-maintenance` with `--enable-lid-hibernate`; those options intentionally describe opposite lid behavior.

The machine this was derived from temporarily used a keyfile embedded into the UKI to allow delegated remote maintenance. That is convenient, but it substantially weakens disk encryption: anyone with the machine and boot partition can often boot it without the disk password. See [docs/security.md](docs/security.md) before enabling anything like that.

The Limine helper preserves boot file hashes by default. Stripping hashes is a recovery-only action for known broken boot entries and may conflict with Secure Boot integrity enforcement.

If recovery access was enabled, disable the managed opt-ins later:

```bash
sudo ./install.sh --user "$USER"
sudo systemctl disable --now sshd.service
sudo reboot
```

## Recovery

Before installing, create a snapshot:

```bash
sudo snapper create --description "before MacBookPro13,3 T1 Omarchy survival kit"
```

Rollback notes are in [docs/rollback.md](docs/rollback.md). Troubleshooting notes are in [docs/troubleshooting.md](docs/troubleshooting.md).

## Status

Working on the tested machine:

- Internal display reaches Hyprland.
- Boot menu no longer requires manual OS selection.
- SDDM autologin starts Omarchy when explicitly enabled.
- Touch Bar works when the T1 DKMS driver is present.
- Internal speakers work with the CS8409 DKMS driver.
- 5 GHz Wi-Fi and iPhone hotspot visibility work with the optional BCM43602 NVRAM override.
- Update hooks preserve the custom changes after Omarchy and package updates.

Still experimental:

- This has only been verified on one MacBookPro13,3.
- Out-of-tree DKMS modules can break after kernel updates.
- Future Omarchy, Hyprland, Aquamarine, Limine, or kernel changes may make parts of this obsolete.
