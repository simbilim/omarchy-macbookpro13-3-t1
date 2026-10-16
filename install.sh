#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: sudo ./install.sh [options]

Options:
  --user USER              Omarchy desktop user. Defaults to SUDO_USER or uid 1000.
  --install-audio-dkms     Install the CS8409 audio DKMS driver from upstream.
  --enable-autologin       Create /etc/sddm.conf.d/autologin.conf.
  --enable-ssh             Enable sshd.service.
  --enable-remote-maintenance
                            Ignore lid/idle events for remote maintenance.
  --enable-lid-hibernate    Hibernate when the lid is closed.
  --enable-bcm43602-5ghz-wifi
                            Install and preserve the Apple BCM43602 Wi-Fi NVRAM override.
  --bcm43602-nvram-file FILE
                            Source NVRAM text file for --enable-bcm43602-5ghz-wifi.
  --preserve-luks-auto-unlock
                            Preserve an existing /crypto_keyfile.bin UKI setup.
  -h, --help               Show this help.

Environment:
  AUDIO_DRIVER_COMMIT      Override the tested snd_hda_macbookpro commit.
  AUDIO_DRIVER_SOURCE_DIR  Override persistent source directory for the audio driver.
EOF
}

orig_args=("$@")
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
run_user="${OMARCHY_USER:-}"
install_audio=0
enable_autologin=0
enable_ssh=0
enable_remote_maintenance=0
enable_lid_hibernate=0
enable_bcm43602_5ghz_wifi=0
preserve_luks_auto_unlock=0
bcm43602_nvram_file="${OMARCHY_BCM43602_NVRAM_FILE:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)
      [[ $# -ge 2 ]] || { echo "FAIL: --user needs a value" >&2; exit 2; }
      run_user="$2"
      shift 2
      ;;
    --install-audio-dkms)
      install_audio=1
      shift
      ;;
    --enable-autologin)
      enable_autologin=1
      shift
      ;;
    --enable-ssh)
      enable_ssh=1
      shift
      ;;
    --enable-remote-maintenance)
      enable_remote_maintenance=1
      shift
      ;;
    --enable-lid-hibernate)
      enable_lid_hibernate=1
      shift
      ;;
    --enable-bcm43602-5ghz-wifi)
      enable_bcm43602_5ghz_wifi=1
      shift
      ;;
    --bcm43602-nvram-file)
      [[ $# -ge 2 ]] || { echo "FAIL: --bcm43602-nvram-file needs a value" >&2; exit 2; }
      bcm43602_nvram_file="$2"
      shift 2
      ;;
    --preserve-luks-auto-unlock)
      preserve_luks_auto_unlock=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "FAIL: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if (( enable_remote_maintenance && enable_lid_hibernate )); then
  echo "FAIL: --enable-remote-maintenance conflicts with --enable-lid-hibernate" >&2
  echo "INFO: remote maintenance ignores lid/idle events; lid hibernate is for mobile safety" >&2
  exit 2
fi

if (( EUID != 0 )); then
  exec sudo bash "$0" "${orig_args[@]}"
fi

detect_user() {
  if [[ -n "$run_user" && "$run_user" != root ]]; then
    printf '%s\n' "$run_user"
    return 0
  fi
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER:-}" != root ]]; then
    printf '%s\n' "$SUDO_USER"
    return 0
  fi
  if getent passwd 1000 >/dev/null 2>&1; then
    getent passwd 1000 | cut -d: -f1
    return 0
  fi
  return 1
}

run_user="$(detect_user)" || {
  echo "FAIL: could not detect the Omarchy desktop user; pass --user USER" >&2
  exit 1
}

user_home="$(getent passwd "$run_user" | cut -d: -f6 || true)"
if [[ -z "$user_home" || ! -d "$user_home" ]]; then
  echo "FAIL: user $run_user does not have a valid home directory" >&2
  exit 1
fi

capture_bcm43602_nvram_source() {
  local input_path="$1" output_path="$2" snapshot sanitized required_line

  if ! command -v perl >/dev/null 2>&1; then
    echo "FAIL: perl is required for a no-follow BCM43602 NVRAM import" >&2
    exit 1
  fi

  snapshot="$(mktemp)"
  sanitized="$(mktemp)"
  chmod 0600 "$snapshot" "$sanitized"

  if ! perl -MFcntl=O_RDONLY,O_NOFOLLOW,:mode -e '
    use strict;
    use warnings;

    my ($src, $dst) = @ARGV;
    sysopen(my $in, $src, O_RDONLY | O_NOFOLLOW)
      or die "open failed: $!\n";
    my @st = stat($in)
      or die "fstat failed: $!\n";
    S_ISREG($st[2])
      or die "not a regular file\n";
    die "unexpected size: $st[7] bytes\n"
      if $st[7] < 1024 || $st[7] > 65536;

    open(my $out, ">", $dst)
      or die "snapshot failed: $!\n";
    binmode($in);
    binmode($out);
    my $buf = "";
    while (1) {
      my $n = sysread($in, $buf, 65536);
      die "read failed: $!\n" unless defined $n;
      last if $n == 0;
      print {$out} $buf or die "write failed: $!\n";
    }
    close($out) or die "close failed: $!\n";
  ' "$input_path" "$snapshot"; then
    rm -f "$snapshot" "$sanitized"
    echo "FAIL: could not safely snapshot BCM43602 NVRAM source" >&2
    exit 1
  fi

  for required_line in \
    '^devid=0x43ba$' \
    '^ccode=00$' \
    '^regrev=245$' \
    '^aa5g=7$' \
    '^txchain=7$' \
    '^rxchain=7$' \
    '^macaddr='; do
    if ! grep -Eq "$required_line" "$snapshot"; then
      rm -f "$snapshot" "$sanitized"
      echo "FAIL: BCM43602 NVRAM source is missing required line: $required_line" >&2
      exit 1
    fi
  done

  awk '
    { sub(/\r$/, "") }
    /^macaddr=/ { print "macaddr=00:00:00:00:00:00"; seen=1; next }
    { print }
    END { if (!seen) print "macaddr=00:00:00:00:00:00" }
  ' "$snapshot" >"$sanitized"

  install -D -m 0644 -o root -g root "$sanitized" "$output_path"
  rm -f "$snapshot" "$sanitized"
}

bcm43602_managed_source="/usr/local/share/macbook-t1-omarchy/brcmfmac43602-pcie-source.txt"
if [[ -n "$bcm43602_nvram_file" ]]; then
  capture_bcm43602_nvram_source "$bcm43602_nvram_file" "$bcm43602_managed_source"
elif (( enable_bcm43602_5ghz_wifi )) && [[ ! -f "$bcm43602_managed_source" ]]; then
  echo "FAIL: --enable-bcm43602-5ghz-wifi needs --bcm43602-nvram-file FILE on first install" >&2
  exit 1
fi

config_tmp="$(mktemp)"
{
  printf 'OMARCHY_USER=%s\n' "$run_user"
  printf 'OMARCHY_ENABLE_AUTOLOGIN=%s\n' "$enable_autologin"
  printf 'OMARCHY_ENABLE_SSH=%s\n' "$enable_ssh"
  printf 'OMARCHY_ENABLE_REMOTE_MAINTENANCE=%s\n' "$enable_remote_maintenance"
  printf 'OMARCHY_ENABLE_LID_HIBERNATE=%s\n' "$enable_lid_hibernate"
  printf 'OMARCHY_ENABLE_BCM43602_5GHZ_WIFI=%s\n' "$enable_bcm43602_5ghz_wifi"
  printf 'OMARCHY_PRESERVE_LUKS_AUTO_UNLOCK=%s\n' "$preserve_luks_auto_unlock"
} >"$config_tmp"
install -D -m 0644 "$config_tmp" /etc/macbook-t1-omarchy.conf
rm -f "$config_tmp"

install -D -m 0755 "$repo_dir/scripts/macbook-t1-omarchy-maintain" /usr/local/sbin/macbook-t1-omarchy-maintain
install -D -m 0755 "$repo_dir/scripts/limine-unattended-fix" /usr/local/sbin/macbook-t1-limine-unattended-fix
install -D -m 0755 "$repo_dir/scripts/dri-symlinks" /usr/local/sbin/macbook-t1-dri-symlinks
install -D -m 0755 "$repo_dir/scripts/install-audio-dkms" /usr/local/sbin/macbook-t1-install-audio-dkms
install -D -m 0755 "$repo_dir/scripts/install-ec-wake-dkms" /usr/local/sbin/macbook-t1-install-ec-wake-dkms
install -D -m 0755 "$repo_dir/scripts/macbook-t1-gpu-pref" /usr/local/sbin/macbook-t1-gpu-pref
install -D -m 0755 "$repo_dir/scripts/macbook-t1-igd-boot-check" /usr/local/sbin/macbook-t1-igd-boot-check
install -D -m 0755 "$repo_dir/scripts/macbook-t1-radeon-off" /usr/local/sbin/macbook-t1-radeon-off

install -D -m 0644 "$repo_dir/hooks/pacman/99-macbook-t1-omarchy-maintain.hook" /etc/pacman.d/hooks/99-macbook-t1-omarchy-maintain.hook
install -D -m 0644 "$repo_dir/systemd/macbook-t1-igd-boot-check.service" /etc/systemd/system/macbook-t1-igd-boot-check.service
install -D -m 0644 "$repo_dir/systemd/macbook-t1-radeon-off.service" /etc/systemd/system/macbook-t1-radeon-off.service

OMARCHY_USER="$run_user" \
OMARCHY_ENABLE_AUTOLOGIN="$enable_autologin" \
OMARCHY_ENABLE_SSH="$enable_ssh" \
OMARCHY_ENABLE_REMOTE_MAINTENANCE="$enable_remote_maintenance" \
OMARCHY_ENABLE_LID_HIBERNATE="$enable_lid_hibernate" \
OMARCHY_ENABLE_BCM43602_5GHZ_WIFI="$enable_bcm43602_5ghz_wifi" \
OMARCHY_PRESERVE_LUKS_AUTO_UNLOCK="$preserve_luks_auto_unlock" \
  /usr/local/sbin/macbook-t1-omarchy-maintain install

if (( install_audio )); then
  AUDIO_DRIVER_COMMIT="${AUDIO_DRIVER_COMMIT:-}" \
  AUDIO_DRIVER_SOURCE_DIR="${AUDIO_DRIVER_SOURCE_DIR:-}" \
    /usr/local/sbin/macbook-t1-install-audio-dkms
fi

echo "Installed MacBookPro13,3 T1 Omarchy survival kit for user: $run_user"
echo "Reboot recommended."
