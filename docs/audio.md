# Audio

The internal speakers on the tested MacBookPro13,3 worked after installing the CS8409 driver from:

https://github.com/davidjo/snd_hda_macbookpro

The tested commit is pinned in `scripts/install-audio-dkms`:

```text
89b22ff90b86468b186706861dd18663562defa7
```

The installer applies the local `patches/cs8409-resume-pr220.patch` to that
pinned commit. It reprograms the codec when its GPIO mask is zero after sleep,
as proposed in [upstream PR #220](https://github.com/davidjo/snd_hda_macbookpro/pull/220).
On this MacBookPro13,3, a deep-sleep resume left the GPIO mask, direction and
data at zero, with silent speakers and microphone. A cold boot restored them
to `0x27`, `0x22` and `0x23` and restored audible speaker output. The patched
DKMS module builds for both installed kernels. On 31 October, the loaded LTS
module detected lost setup after each of two S3 resumes, reprogrammed the
codec, and restored the GPIO mask to `0x27`. A microphone loopback recording
picked up the test tone after the first resume. Both open-lid S3 tests woke
after only a few seconds, leaving the USB-C controllers absent; avoid repeating
that short test. A normal, longer lid-close cycle and user confirmation of
audible playback after resume are still needed.

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

The CS8409/CS42L83 path on this model is effectively a 44.1 kHz hardware path.
The mobile profile installs this PipeWire drop-in so the PipeWire graph matches
the codec instead of running the graph at 48 kHz and resampling at the sink:

```text
/etc/pipewire/pipewire.conf.d/90-macbook-t1-cs8409-rate.conf
```

The mobile profile also installs a conservative protected speaker sink:

```text
/etc/pipewire/pipewire.conf.d/91-macbook-t1-speaker-protect.conf
```

It keeps the desktop-facing sink stereo, adds headroom, cuts sub-bass, and
trims the low band before sending audio to the real internal speaker sink. This
does not reproduce Apple's per-speaker CoreAudio processing, but it reduces
speaker stress on the current Linux stereo path.

If sound is still missing:

```bash
sudo dmesg | grep -Ei 'cs8409|snd|hda|cirrus'
systemctl --user status pipewire wireplumber
wpctl status
```

Avoid high-volume direct `hw:` or `plughw:` speaker tests. Use PipeWire/WirePlumber and start with low volume.

## Four-driver speaker DSP (2026-11-05)

Replaces `91-macbook-t1-speaker-protect.conf` (removed from `/etc`, still in the repo as fallback).

Measured with internal-mic log sweeps on the `analog-surround-40` sink:
FL = left tweeter, FR = right tweeter, RL = left woofer, RR = right woofer
(same mapping as MacBookPro14,3 in davidjo/snd_hda_macbookpro issue #213).
The stereo profile drives each side's woofer and tweeter full-range; both
overlap at 2-5 kHz and produced a ~8 dB peak at 2.5 kHz.

- `pipewire/93-macbook-t1-speaker-dsp.conf` -> `/etc/pipewire/pipewire.conf.d/`:
  sink `macbook_t1_speakers` ("MacBook Speakers"): -1 dB, LSP lookahead limiter
  at -3 dBFS (needs `lsp-plugins-lv2`), LR4 crossover at 2.5 kHz, woofer
  120 Hz high-pass + 3 dB low shelf, tweeter +4 dB shelf above 4.5 kHz,
  tweeter -1.5 dB and inverted polarity (summed better at the crossover on both sides).
- `scripts/macbook-t1-speaker-router` -> `/usr/local/bin/`, user unit
  `systemd/macbook-t1-speaker-router.service`: headphones plugged -> stereo
  profile (the 4.0 profile has no headphone port); otherwise 4.0 profile and
  default sink `macbook_t1_speakers`. Does not touch a non-built-in default sink.
- Omarchy 4.5 volume keys resolve through the DSP sink to the hardware 4.0
  sink (`omarchy-audio-output-sink`), so the keys set the hardware level. The
  router pins the "MacBook Speakers" input at 50% (-18 dB). Tested 2026-11-05:
  no crackle with the keys at 100%.
- Persistence: `/etc` drop-ins are not package-owned. `install-mobile-profile`
  installs `lsp-plugins-lv2`, the DSP, the router and enables the user unit
  globally. `macbook-t1-omarchy-maintain` (pacman hook on pipewire, wireplumber,
  omarchy, ...) removes stale 91/92 drop-ins, re-enables the router and warns
  when the limiter plugin is missing or an Omarchy speaker tuning is active.

The internal mic sits next to the left drivers and has its own coloration, so
the measurements are only valid for channel identity, polarity and relative
before/after comparisons. Final balance is by ear.

Rollback: `sudo systemctl --global disable macbook-t1-speaker-router` and
`systemctl --user stop macbook-t1-speaker-router`, remove `93-…`, reinstall
`91-…`, restart pipewire, set profile `output:analog-stereo+input:analog-stereo`.
