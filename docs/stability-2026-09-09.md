# MacBookPro13,3 stability investigation, 9 September 2026

Hibernation failure was reproduced on both kernels and the replacement s2idle path now passes complete systemd tests on AC and battery, with Radeon `profile_standard` and the repaired Touch Bar driver. The user confirmed operation after the repaired AC wake and the physical battery lid-close/open test. Battery operation, a bounded load test, a reboot and actual YouTube app launch passed. The lid test included one short intermediate wake followed by automatic resuspend; its trigger is not established. A fully powered-off start on battery remains pending.

## Evidence from 8–9 September

- 8 September, 09:12–16:37: a long desktop session, ending when lid close requested hibernation.
- 8 September, 17:16: a fresh boot on battery reported CPU machine-check records. This followed the earlier hibernation attempt, but the logs alone do not establish causation or defective hardware.
- 8 September, 17:18: another lid close requested hibernation. The following boots reported no hibernation image.
- 8 September, 19:59 and 20:00: boot logs stopped before the graphical session, on battery.
- 9 September, 08:51 and 08:52: similarly incomplete boots occurred on AC power.
- 8 September, 09:04, and 9 September, 08:53: Radeon graphics/SDMA ring timeouts were followed by GPU reset attempts and display-controller timeouts.
- The internal Apple SPI keyboard was registered in every inspected boot, including the failed evening boots. This does not prove every key worked, but there is no evidence of an absent keyboard driver.

The existing `Omarchy Rescue - Safe Graphics` and ordinary `linux` entries both used the same `omarchy_linux.efi`, kernel `7.1.9-arch1-2`, and the same Radeon/PCIe stability flags. The boot-entry name did not select an older OS version.

## Baseline health

The initial accessible session had no failed system or user services, matching installed DKMS modules, ample disk space, and zero Btrfs device error counters. Battery telemetry reported 12 cycles and full-charge capacity close to design capacity. Idle CPU/GPU temperatures were within normal limits. These checks do not rule out intermittent hardware faults.

## Tests and changes

| Test/change | Result |
| --- | --- |
| Root Snapper checkpoint | Snapshot 25, before changes |
| Four-scene glmark2 on kernel 7.1.9 | Completed; no recorded new GPU fault during the benchmark |
| Hibernation process-freezer test, twice | Returned successfully |
| Hibernation device test on 7.1.9 | Failed: Radeon SMU firmware reload and device restore error `-22`; subsequent SDMA timeout and visible pixel corruption |
| Install `linux-lts` and `linux-lts-headers` | Installed 6.18.46 alongside the existing kernel; audio and Touch Bar DKMS builds succeeded |
| Add first boot entry `Omarchy LTS - MacBook` | Added from the generated LTS entry, with its image hash verified; original entries retained |
| First LTS boot and four-scene glmark2 | Desktop and benchmark worked; internal input and driver services present; no new GPU faults recorded |
| Hibernation freezer/device test on LTS with `pm_async=0` | Freezer returned; device restore still failed with Radeon SMU firmware reload error `-22` |
| Two s2idle device tests, Thunderbolt NHI unloaded and `pm_async=0` | Both returned without GPU errors |
| Direct RTC s2idle test, 09:29 | Returned after 42 seconds; network reconnected; Hyprland and a post-wake graphics benchmark worked |
| Touch Bar after that sleep | User reported missing buttons; restarting the installed T1 activation service restored the strip |
| YouTube launch, 09:35 | Session stopped at Chromium launch; no recorded fault establishes the precise crash cause |
| Chromium with all GPU acceleration disabled | No new crash observed, but user reported choppy video |
| Chromium with explicit Radeon render node, ANGLE OpenGL, software video decode | Local 1080p60 test: 7 dropped of 2,454 frames. YouTube 1080p60: 2,372 subsequent frames with no drops; user confirmed smooth playback |
| Full systemd suspend test, 09:48–09:55 | Entered s2idle and resumed in the same boot, without Radeon errors. The test harness wrongly cancelled the RTC alarm before asynchronous suspend started. Manual wake returned the desktop. Post-resume Touch Bar activation triggered a driver warning and exceeded the system-wide 5-second stop timeout |
| Touch Bar source diagnosis | `.suspend` and `.reset_resume` were registered, but `.resume` was missing. Normal wake left the driver inactive and the strip dark. USB reconfiguration in the activation script then reprobed an input handler that had not been unregistered |
| Reboot with repaired Touch Bar driver | Automatic LTS boot succeeded; loaded module matched rebuilt module; no failed services |
| Next normal sleep request, 10:05 | Omarchy requested its lock screen at 10:05:06; SDMA0 timed out at 10:05:10, before suspend started. The GPU hang subsequently prevented process freezing. This is a separate runtime graphics fault, not evidence that the Touch Bar resume callback failed |
| Temporary Radeon `profile_standard`, then lock, 10:12 | Lock secured successfully; no new GPU error recorded. This profiling mode disables clock/power gating. Further sleep, battery and restart validation is pending |
| Full systemd sleep with `profile_standard`, 10:13:49–10:14:20 | Entered and exited s2idle in the same boot, without GPU faults or failed units. User processes froze and thawed normally. The alarm remained armed; wake occurred before its deadline, so RTC-triggered wake is not established |
| Touch Bar readiness diagnosis after that cycle | The new callback was present in the loaded module, but no resume message appeared. Its readiness guard still required both mode and display interfaces; the installed driver's own T1 activation/display code explicitly identifies T1 as having only the mode interface. Added the same T1 exception to resume |
| Reboot at 10:25 with complete T1 guard and persistent GPU profile | Automatic LTS boot succeeded. The loaded Touch Bar module matched the rebuilt one, `profile_standard` was active, Hyprland was running and no units had failed |
| CPU/memory load in Performance energy mode | Four CPU workers at 70% plus a verified 1 GiB memory worker ran for 24.8 seconds before the test's 92 °C guard stopped them. No calculation errors, machine checks or GPU faults were recorded. This is an abbreviated test, not a full-duration pass or proof of a cooling fault |
| Bounded CPU/memory verification in Balanced energy mode | Two CPU workers at 50% plus a verified 1 GiB memory worker completed 45.8 seconds. No verification errors, machine checks or GPU faults. Sampled package temperatures reached 88 °C; the 92 °C guard was not triggered. This checks a limited workload, not all memory or long-term hardware reliability |
| Full sleep with the complete T1 fix, 10:28:34–10:29:26 | Same boot resumed, no failed units or GPU faults. Kernel logged both `Touchbar suspended` and `Touchbar resumed`; user confirmed that it worked. GPU mode remained `profile_standard` and async callbacks were restored |
| Battery operation with all cables removed | AC telemetry changed to disconnected, battery to discharging, external keyboard disappeared and Wi-Fi remained reachable. User reported that operation looked good |
| Bounded CPU/memory verification on battery | The same two-worker/1 GiB Balanced test completed 45.8 seconds, without calculation errors, machine checks or GPU faults. Sampled package temperatures remained below 70 °C |
| Reboot without power or external keyboard, 10:32 | Automatic LTS boot succeeded on battery, with the repaired Touch Bar service, Radeon `profile_standard` and Balanced energy mode. No failed units or new machine-check/GPU faults |
| Actual YouTube web-app launch on battery, 10:38 | The ordinary Omarchy launcher opened the app. Its main Chromium process contained all four persisted renderer/video flags. No GPU or machine-check faults were recorded. The first remote launch attempt had ended its helper too soon; keeping the systemd test unit alive for its child processes corrected the test harness |
| Complete systemd sleep on battery with YouTube open, 10:41:23–10:42:16 | Same boot resumed; suspend returned success. Touch Bar suspended and resumed normally, `profile_standard` stayed active and async callbacks were restored. No GPU faults or failed units |
| Graphics after that battery wake | Two off-screen glmark2 scenes completed for 20 seconds on the Radeon, score 1,562 for this workload. No new GPU faults, machine checks or failed services. Btrfs device error counters remained zero. This score is not directly comparable with the earlier four-scene test |
| Physical lid close/open on battery, 10:57:36–11:04:55 | Logind recorded the lid closing and requested suspend. The first sleep returned at 10:57:51 while the lid remained closed, with no recorded device failure; logind suspended again at 10:58:07. It remained in that sleep until the lid opened at 11:04:54, then resumed in the same boot. Touch Bar resumed on both wake paths; user confirmed that the requested physical test worked. No new GPU/CPU faults or failed services; all suspend failure counters were zero. The first intermediate wake's trigger is unknown |
| Touch Bar remained lit during display idle | The user reported a black screen with the Touch Bar still active. DRM confirmed panel DPMS `Off`; the Touch Bar's module defaults and live idle policy were both `-1` (always on). Added a separate display-state service using the existing live `idle_timeout=-2` control. A controlled screen-on/off cycle at 11:27 confirmed restoration to `-1` on DPMS `On` and deactivation to `-2` on DPMS `Off`, without a USB reset, driver reload or new kernel error. The original off state was restored after the test; visual confirmation at the laptop was requested |
| Brief line at the boot-logo transition | The user reported a short disruptive line near the lower screen around the Plymouth logo. The inspected boot had no GPU faults, but showed firmware/simpledrm, Radeon and later Intel initialization. This suggests a possible display handover artifact; it does not establish the visual cause. Added the experimental `zz-macbook-t1-early-kms.conf` drop-in, preserving existing modules and appending `amdgpu i915`, to request earlier driver loading. Both kernel images rebuilt successfully; their embedded build configuration contains both added modules, and the preferred LTS entry's image hash passes verification |
| First early-KMS reboot, 11:44 | Automatic LTS boot and desktop succeeded, required services were active and no system/user units or GPU/CPU faults were recorded. The user reported improvement, with one remaining narrow vertical bar of roughly 10–20 pixels near the logo. This is partial visual improvement, not resolution. Journal events still place Intel DRM registration after the main-system Plymouth service start, so the module list does not prove all display initialization finishes before the splash. The original theme also contains a progress bar initially one pixel wide and ten pixels high; its relevance depends on the artifact's exact position and timing. The theme has not been changed. A repeat boot with identical settings was requested by the user for camera capture |
| Repeat early-KMS reboot for camera capture, 11:49:57 | The user explicitly reported that the flash was gone. No runtime or theme changes were made between this and the first early-KMS boot. Automatic LTS startup and Hyprland succeeded; Touch Bar activation/display-state services and Radeon protection were active, `profile_standard` remained selected, and no failed system/user units or new GPU/CPU faults were recorded. Retained the early-KMS drop-in. This confirms a clean observed startup; the mixed first/second observations do not establish the precise mechanism or guarantee every future startup |

The hibernation device test returning to the shell is **not** a pass: the kernel logged a failed GPU restore and the desktop was damaged. Both attempts needed recovery. Test controls were restored to `pm_test=none` and the original async setting.

## Follow-up, 21–22 September 2026

The later mobile investigation supersedes the Radeon-based configuration described below. Omarchy 4.0.4 now boots `linux-lts` 6.18.49-3 by default on Intel graphics. `linux-omarchy` 7.2.5-3 remains as the Safe Graphics and Console rescue kernel; the ordinary Arch `linux` package and headers were removed. The preferred-entry helper verifies the LTS image and keeps the two rescue entries on the current `linux-omarchy` image with fresh BLAKE2 hashes.

Actual cold hibernation restore resets before userspace on both retained kernels. Deep/S3 returns the display but Apple firmware removes both Alpine Ridge PCIe trees, losing the USB-C controllers. Both modes are therefore disabled for normal lid operation. The one-off initramfs resume hook and kernel diagnostic module used to locate the hibernation failure are not part of the final configuration.

The retained path is s2idle with Intel-only graphics. Before suspend the helper explicitly selects s2idle, serializes device callbacks, unloads the unused Thunderbolt NHI and suppresses the three xHCI wake sources only while the lid is closed. It restores those settings after wake and powers the unused Radeon back down through GMUX. A 103-second controlled test on AC resumed the same Hyprland process, retained both USB-C controllers and USB networking, and produced no failed unit or xHCI resume error. The final disconnected lid test then stayed in one suspend for 5,409 seconds, resumed that same boot/session, lost 61 mAh and measured about 0.515 W average draw. Both USB-C controllers and all tested services remained healthy, with zero kernel suspend failures.

The Apple SPI keyboard now has a model-specific libinput quirk that marks it internal. A fresh compositor context reports disable-while-typing enabled, addressing the concrete keyboard/touchpad pairing fault without changing pointer speed or gesture behavior.

After acceptance, historical snapshots were reduced to two: one rollback from before the refinement and one snapshot of the measured stable state. Limine shows only LTS inside those snapshots. A final unattended reboot selected `6.18.49-3-lts`, reached Hyprland on Intel, verified all managed UKI hashes and reported no failed systemd units.

## Current changes

- `linux-lts` 6.18.46 and its headers are installed alongside the original kernel; both audio and Touch Bar DKMS modules built successfully.
- The first Limine entry is `Omarchy LTS - MacBook`. The preferred-entry helper validates the generated UKI's BLAKE2 hash and copies its settings. A post-build hook refreshes it when the generated image changes. Fixture tests cover idempotence, stale-hash replacement and refusal of invalid/ambiguous input.
- Hibernation is disabled because of the reproduced Radeon resume failure. The mobile profile selects s2idle and serial device callbacks, removes unused Thunderbolt NHI before sleep, and restores NHI after wake. Its stop timeout is explicitly 30 seconds instead of the system-wide 5 seconds.
- The T1 driver now calls its state-restoration logic on normal resume as well as reset-resume, and accepts T1's single mode interface as ready. Normal resume preserves the existing USB runtime-PM reference; reset-resume reacquires it. The post-sleep USB reconfiguration workaround was removed. DKMS builds are applied to both installed kernels and the kernel images regenerated. The package-update hook reapplies the source fix if the driver package replaces it. Snapshot 26 precedes this driver change. Source-migration fixtures cover original/previous local versions, idempotence and refusal of unexpected source.
- A separate `macbook-t1-touchbar-display.service` follows internal-panel DPMS through DRM sysfs and temporarily disables the Touch Bar while the panel is off. It restores the prior per-device idle policy when the panel returns, or when the service stops, and keeps newer user changes. This does not change the driver or its module defaults. It is enabled at graphical startup and included in the mobile-profile installer.
- The Radeon D3cold service now applies the stock `profile_standard` performance mode before the display manager starts. This disables clock/power gating without voltage or overclock changes. The mode survived the successful sleep cycle. Battery runtime impact is unmeasured.
- The laptop's system energy profile was changed from Performance to Balanced through `powerprofilesctl`. This is separate from the Radeon profiling mode. The mobile installer does not override the user's system energy profile.
- Balanced was active during the battery tests. After reconnecting AC, the current profile returned to Performance; the installed Omarchy power-profile helper selects Performance by default on AC. No persistent AC-profile override was made during the splash investigation.
- Chromium's existing user flags are preserved, with four tested settings added: `--render-node-override=/dev/dri/by-path/pci-0000:01:00.0-render`, `--use-gl=angle`, `--use-angle=gl`, and `--disable-accelerated-video-decode`. GPU rendering remains enabled. The Radeon VA-API capabilities list H.264/HEVC, but not VP9/AV1.
- The initial root rollback point is snapshot 25; snapshot 26 precedes the Touch Bar driver work. Snapshot 27 captures the applied fixes after the AC and battery tests above. Snapshot 28 additionally includes the Touch Bar display-state service after its on/off policy test. Boot and managed configuration backups were also made separately on the laptop. Root snapshots do not cover the separate `/boot` filesystem or the user's Chromium flags; those have their own file backups.
- Snapshot 29 precedes the early-KMS splash change; snapshot 30 captures the retained configuration after the clean observed repeat boot. The matching file under `mkinitcpio/` is installed on the laptop but is not yet included in the mobile-profile installer. No splash artwork, screen resolution, kernel arguments or Plymouth renderer settings were changed. To undo the early-KMS change, remove only `/etc/mkinitcpio.conf.d/zz-macbook-t1-early-kms.conf`, run `sudo limine-mkinitcpio`, then verify with `sudo /usr/local/sbin/macbook-t1-preferred-kernel --check`. Restoring an old boot-menu file alone would not restore the rebuilt images.

## Pending

- Watch ordinary future startups for recurrence of the boot-logo artifact. The user confirmed the flash was absent on the second early-KMS boot; the preceding boot had still shown a reduced artifact. Further splash/theme changes were not needed for the clean observed boot.
- Observe longer daily use, including a fully powered-off start on battery. Warm restarts passed on AC and battery; that does not establish every cold-start case.
- Watch for repeated wakes while the lid remains closed. One intermediate wake occurred in the physical test, followed by automatic resuspend and a successful wake on lid opening; no failure or wake-source diagnosis was recorded.
- Continue watching for recurrence of the historical CPU machine-check records; the bounded CPU/memory tests did not reproduce them.

## References

- [Linux kernel power-management test stages](https://www.kernel.org/doc/html/latest/power/basic-pm-debugging.html)
- [Model-specific Linux support notes](https://github.com/Dunedan/mbp-2016-linux#suspend--hibernation)
- [Separate MacBookPro13,3 s2idle investigation, 6 September comment](https://github.com/omacom/omarchy/discussions/4695)
- [Chromium render-node override implementation](https://chromium.googlesource.com/chromium/src/+/41794268dcb69d0f30bb158ccc86dffb1e942af0)
- [Chromium VA-API verification](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/gpu/vaapi.md)
- [AMDGPU performance profiles](https://docs.kernel.org/gpu/amdgpu/thermal.html)

No private logs, device identifiers, network addresses, encryption material, or firmware calibration data are included here.
