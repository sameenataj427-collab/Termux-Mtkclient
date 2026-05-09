import os
import sys
import subprocess
import time

def start_universal_bypass():
    print("--- MTK Universal Termux Bridge ---")
    print("Waiting for device in BROM mode...")
    
    while True:
        try:
            output = subprocess.check_output(["termux-usb", "-l"]).decode().strip()
            if "/dev/bus/usb/" in output:
                address = ""
                for line in output.split('\n'):
                    if "/dev/bus/usb/" in line:
                        address = line.strip()
                        break
                
                if address:
                    print(f"\n[!] Found: {address}")
                    print("[*] REQUESTING PERMISSION... ACCEPT THE POPUP!")
                    
                    # -e flag executes the script immediately upon permission grant
                    cmd = f"termux-usb -r {address} -e 'export TERMUX_USB_FD=$1; python3 mtk_main.py {' '.join(sys.argv[1:])}'"
                    os.system(cmd)
                    return 
                    
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            pass
        time.sleep(0.1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mtk.py printgpt --loader mtkclient/Loader/MTK_DA_V6.bin")
    else:
        start_universal_bypass()
