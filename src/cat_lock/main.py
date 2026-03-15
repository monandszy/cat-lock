import sys
from cat_lock.system import inhibit_sleep, SystemKeyBlocker
from cat_lock.downloader import ensure_cat_image
from cat_lock.app import run_lock_screen

def cli_entry():
    # If explicitly asked to download via "cat-lock download"
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        ensure_cat_image()
        return

    # Block sleep
    if len(sys.argv) < 2 or sys.argv[1] != "inhibited":
        if inhibit_sleep():
            return
        
    # Apply lock screen with system keys disabled via Context Manager
    with SystemKeyBlocker():
        run_lock_screen()