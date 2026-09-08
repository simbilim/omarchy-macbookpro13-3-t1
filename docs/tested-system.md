# Tested System

This was verified on one machine.

## DMI

```text
product_name=MacBookPro13,3
product_version=1.0
board_name=Mac-A5C67F76ED83108C
board_vendor=Apple Inc.
```

## Relevant PCI Devices

```text
00:02.0 VGA compatible controller [0300]: Intel Corporation Skylake-H GT2 [HD Graphics 530] [8086:191b]
03:00.0 Network controller [0280]: Broadcom Inc. and subsidiaries BCM43602 802.11ac Wireless LAN SoC [14e4:43ba]
00:1f.3 Audio device [0403]: Intel Corporation 100/C230 Series Chipset Family HD Audio [8086:a170]
01:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Baffin [Radeon RX 460/560D / Pro 450/455/460/555/555X/560/560X] [1002:67ef]
01:00.1 Audio device [0403]: Advanced Micro Devices, Inc. [AMD/ATI] Baffin HDMI/DP Audio [Radeon RX 550 640SP / RX 560/560X] [1002:aae0]
```

## Verified Working

- Omarchy `4.0.2`
- Kernel `7.1.9-arch1-2`
- Hyprland internal panel through the Radeon GPU
- Touch Bar with `apple-ib-drv/0.1` DKMS present
- Speakers with `snd_hda_macbookpro/0.1` DKMS present
- 5 GHz Wi-Fi and iPhone Personal Hotspot visibility with the optional BCM43602 NVRAM override
- Limine boot menu unattended default entry
- SDDM autologin into Omarchy session when explicitly enabled

## Not Yet Verified

- Other MacBookPro13,x variants
- External displays
- Suspend and resume over long periods
- T2 Macs
- Apple Silicon Macs
