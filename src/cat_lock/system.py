import sys
import os
import subprocess
import atexit

def inhibit_sleep() -> bool:
    """Relaunches the script wrapped in systemd-inhibit. Returns False if unsupported."""
    if len(sys.argv) > 1 and sys.argv[-1] == "inhibited":
        return True 

    print("Activating sleep block and cat shield...")
    try:
        args = ["systemd-inhibit", 
                "--what=sleep:idle", 
                "--who=CatShield", 
                "--why=Waiting for user input", 
                sys.executable] + sys.argv + ["inhibited"]
        
        os.execvp(args[0], args)
    except FileNotFoundError:
        print("systemd-inhibit not found, continuing without sleep block...")
        return False
    return True

GNOME_KEYS_TO_DISABLE = [
    ("org.gnome.mutter", "overlay-key", "''"),
    ("org.gnome.desktop.wm.keybindings", "switch-applications", "[]"),
    ("org.gnome.desktop.wm.keybindings", "switch-applications-backward", "[]"),
    ("org.gnome.desktop.wm.keybindings", "switch-windows", "[]"),
    ("org.gnome.desktop.wm.keybindings", "switch-windows-backward", "[]"),
    ("org.gnome.desktop.wm.keybindings", "cycle-windows", "[]"),
    ("org.gnome.desktop.wm.keybindings", "cycle-windows-backward", "[]"),
    ("org.gnome.shell.keybindings", "toggle-overview", "[]"),
]

UBUNTU_DEFAULT_KEYS =[
    ("org.gnome.mutter", "overlay-key", "'Super_L'"),
    
    ("org.gnome.desktop.wm.keybindings", "switch-applications", "['<Super>Tab']"),
    ("org.gnome.desktop.wm.keybindings", "switch-applications-backward", "['<Shift><Super>Tab']"),
    
    ("org.gnome.desktop.wm.keybindings", "switch-windows", "['<Alt>Tab']"),
    ("org.gnome.desktop.wm.keybindings", "switch-windows-backward", "['<Shift><Alt>Tab']"),
    
    ("org.gnome.desktop.wm.keybindings", "cycle-windows", "['<Alt>Escape']"),
    ("org.gnome.desktop.wm.keybindings", "cycle-windows-backward", "['<Shift><Alt>Escape']"),
    ("org.gnome.shell.keybindings", "toggle-overview", "['<Super>s']"),
]


class SystemKeyBlocker:
    """Context manager to disable and restore GNOME shortcuts and brightness to defaults."""
    def __init__(self):
        self.original_brightness = []

    def _get_brightness_files(self):
        """Find brightness control files in sysfs."""
        paths = []
        base = "/sys/class/backlight/"
        if os.path.exists(base):
            for dev in os.listdir(base):
                sys_path = os.path.join(base, dev, "brightness")
                if os.path.isfile(sys_path) and os.access(sys_path, os.W_OK):
                    paths.append(sys_path)
        return paths

    def _set_brightness_low(self):
        self.original_brightness = []
        for sys_path in self._get_brightness_files():
            try:
                with open(sys_path, "r") as f:
                    current = f.read().strip()
                self.original_brightness.append((sys_path, current))
                with open(sys_path, "w") as f:
                    f.write("1")
            except Exception as e:
                print(f"Warning: Failed to lower brightness for {sys_path}: {e}")

    def _restore_brightness(self):
        for sys_path, original_val in self.original_brightness:
            try:
                with open(sys_path, "w") as f:
                    f.write(original_val)
            except Exception as e:
                print(f"Warning: Failed to restore brightness for {sys_path}: {e}")
        self.original_brightness.clear()

    def _restore_defaults(self):
        """Restores keybindings to Ubuntu defaults and handles brightness."""
        print("\nRestoring system shortcuts to Ubuntu defaults...")
        for schema, key, default_val in UBUNTU_DEFAULT_KEYS:
            try:
                subprocess.run(
                    ["gsettings", "set", schema, key, default_val],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"  ✓ Restored '{key}' to default.")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ ERROR: Failed to restore default for '{schema} {key}'.")
                print(f"    Value to restore was: {default_val}")
                print(f"    Stderr from gsettings: {e.stderr.strip()}")

        self._restore_brightness()
        print("Shield removed, sleep and display settings restored.")

    def __enter__(self):
        print("Disabling system shortcuts (Alt+Tab, Super)...")
        self._set_brightness_low()

        for schema, key, disabled_val in GNOME_KEYS_TO_DISABLE:
            try:
                subprocess.run(["gsettings", "set", schema, key, disabled_val], check=True)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"Warning: Could not disable '{key}'. Skipping. Error: {e}")

        atexit.register(self._restore_defaults)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        atexit.unregister(self._restore_defaults)
        self._restore_defaults()