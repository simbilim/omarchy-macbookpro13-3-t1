-- MacBookPro13,3 T1 graphics block for Omarchy Hyprland Lua config.
-- Add to ~/.config/hypr/hyprland.lua, or let install.sh add it.

-- EFI routes the internal panel to Intel; keep the compositor off the Radeon
-- so vga_switcheroo can power the discrete GPU down before suspend.
-- EFI routes the internal panel to Intel; keep the compositor off the Radeon.
hl.env("AQ_DRM_DEVICES", "/dev/dri/intel-igpu")
hl.env("AQ_NO_MODIFIERS", "1")
hl.env("HYPRLAND_EGL_NO_MODIFIERS", "1")
