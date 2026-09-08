# Audio

The internal speakers on the tested MacBookPro13,3 worked after installing the CS8409 driver from:

https://github.com/davidjo/snd_hda_macbookpro

The tested commit is pinned in `scripts/install-audio-dkms`:

```text
89b22ff90b86468b186706861dd18663562defa7
```

Install:

```bash
sudo ./install.sh --user "$USER" --install-audio-dkms
sudo reboot
```

Security note: installing this driver executes third-party code as root. The helper clones into a fresh root-owned staging directory, disables Git hooks before checkout, verifies the pinned commit before running the upstream installer, and checks that the DKMS source symlink points at the persistent verified checkout. You still need to trust that upstream source.

The default persistent source path is:

```text
/opt/macbook-t1/snd_hda_macbookpro-89b22ff90b86468b186706861dd18663562defa7
```

The helper refuses unmanaged existing source directories instead of running Git commands inside them as root. If you previously tested another checkout in that location, move it aside or pass a different trusted absolute `AUDIO_DRIVER_SOURCE_DIR`.

Check status:

```bash
dkms status
modinfo -F filename snd_hda_codec_cs8409
wpctl status
```

Expected DKMS line:

```text
snd_hda_macbookpro/0.1, KERNEL_VERSION, x86_64: installed
```

If sound is still missing:

```bash
sudo dmesg | grep -Ei 'cs8409|snd|hda|cirrus'
systemctl --user status pipewire wireplumber
wpctl status
```

Avoid high-volume direct `hw:` or `plughw:` speaker tests. Use PipeWire/WirePlumber and start with low volume.
