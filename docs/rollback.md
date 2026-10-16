# Rollback

Create a snapshot before installing:

```bash
sudo snapper create --description "before MacBookPro13,3 T1 Omarchy survival kit"
```

If the machine still boots, remove the installed files:

```bash
sudo systemctl disable --now macbook-t1-limine-unattended-fix.path || true
sudo systemctl disable macbook-t1-dri-symlinks.service macbook-t1-radeon-off.service || true
sudo systemctl disable --now macbook-t1-touchbar-display.service || true

sudo rm -f /usr/local/sbin/macbook-t1-omarchy-maintain
sudo rm -f /usr/local/sbin/macbook-t1-limine-unattended-fix
sudo rm -f /usr/local/sbin/macbook-t1-dri-symlinks
sudo rm -f /usr/local/sbin/macbook-t1-preferred-kernel
sudo rm -f /usr/local/sbin/macbook-t1-radeon-off
sudo rm -f /usr/local/sbin/macbook-t1-sleep
sudo rm -f /usr/local/sbin/macbook-sleep-diagnostics
sudo rm -f /usr/local/sbin/macbook-t1-touchbar-display
sudo rm -f /usr/local/sbin/macbook-t1-touchbar-resume-fix
sudo rm -f /usr/local/sbin/macbook-t1-install-audio-dkms
sudo modprobe -r macbook_t1_ec_wake || true
sudo dkms remove -m macbook-t1-ec-wake -v 0.1 --all || true
sudo rm -f /usr/local/sbin/macbook-t1-install-ec-wake-dkms
sudo rm -f /etc/modules-load.d/macbook-t1-ec-wake.conf
sudo rm -rf /usr/src/macbook-t1-ec-wake-0.1
sudo rm -f /etc/boot/hooks/post.d/80-macbook-t1-rescue-defaults
sudo rm -f /etc/boot/hooks/post.d/81-macbook-t1-preferred-kernel
sudo rm -f /etc/systemd/system/macbook-t1-limine-unattended-fix.service
sudo rm -f /etc/systemd/system/macbook-t1-limine-unattended-fix.path
sudo rm -f /etc/systemd/system/macbook-t1-dri-symlinks.service
sudo rm -f /etc/systemd/system/macbook-t1-radeon-off.service
sudo rm -f /etc/systemd/system/macbook-t1-touchbar-display.service
sudo rm -f /etc/systemd/system/systemd-suspend.service.d/90-macbook-t1.conf
sudo rm -f /etc/systemd/system/systemd-suspend.service.d/95-macbook-sleep-diagnostics.conf
sudo rm -f /etc/systemd/system/sddm.service.d/20-macbook-t1-dri-ordering.conf
sudo rm -f /etc/systemd/logind.conf.d/99-macbook-t1-remote-maintenance.conf
sudo rm -f /etc/systemd/logind.conf.d/90-macbook-t1-mobile-lid.conf
sudo rm -f /etc/systemd/logind.conf.d/91-macbook-t1-suspend.conf
sudo rm -f /etc/systemd/sleep.conf.d/91-macbook-t1-deep.conf
sudo rm -f /etc/udev/rules.d/61-macbook-t1-gpu-names.rules
sudo rm -f /etc/libinput/local-overrides.quirks
sudo rm -f /etc/systemd/user/xdg-desktop-portal-hyprland.service.d/90-macbook-pipewire-lifecycle.conf
sudo rm -f /etc/mkinitcpio.conf.d/zz-macbook-t1-early-kms.conf
sudo rm -f /etc/limine-entry-tool.d/macbook13-stability.conf
sudo rm -f /etc/pacman.d/hooks/99-macbook-t1-omarchy-maintain.hook
sudo rm -f /etc/sddm.conf.d/autologin.conf
sudo rm -f /etc/NetworkManager/conf.d/90-macbook-t1-brcmfmac.conf
sudo rm -f /usr/lib/firmware/updates/brcm/brcmfmac43602-pcie.txt
sudo rm -f "/usr/lib/firmware/updates/brcm/brcmfmac43602-pcie.Apple Inc.-MacBookPro13,3.txt"
sudo rm -f /usr/local/share/macbook-t1-omarchy/brcmfmac43602-pcie-source.txt
sudo rm -f /var/lib/macbook-t1-omarchy/brcmfmac43602-5ghz.sha256
sudo rm -f /etc/macbook-t1-omarchy.conf
sudo rm -f /var/lib/macbook-t1-omarchy/pending-uki-rebuild
sudo rm -rf /opt/macbook-t1/snd_hda_macbookpro-89b22ff90b86468b186706861dd18663562defa7

sudo systemctl daemon-reload
sudo limine-mkinitcpio
sudo reboot
```

The installer edits `~/.config/hypr/hyprland.lua` by adding a marked block. Remove this block manually if you roll back:

```lua
-- BEGIN MacBookPro13,3 T1 graphics
...
-- END MacBookPro13,3 T1 graphics
```

Also remove the marked `MacBookPro13,3 T1 trackpad` block from
`~/.config/hypr/input.lua`, run `hyprctl reload`, and run
`systemctl --user daemon-reload` to restore the default tap-and-drag and portal
lifecycle behavior.

If the machine does not boot, use Snapper from the boot menu or a rescue environment and roll back to the snapshot you created before installing.
