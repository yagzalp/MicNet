import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import time
import threading
import sys
import app as m

Gtk.init([])

thread_errors = []
threading.excepthook = lambda args: thread_errors.append(f"{args.exc_type.__name__}: {args.exc_value}")

app = m.MicNetApp()
app.window.hide()

SAMPLE = {
    "url": "https://example.com",
    "host": "example.com",
    "domain": "example.com",
    "email": "test@example.com",
    "ip": "8.8.8.8",
    "entry": "example.com",
    "target": "192.168.1.1",
    "gateway": "192.168.1.1",
    "iface": "lo",
    "username": "admin",
    "bssid": "00:11:22:33:44:55",
    "interface": "wlan0",
}


def autofill(tab):
    for attr, val in tab.__dict__.items():
        if isinstance(val, Gtk.Entry):
            for key, sample in SAMPLE.items():
                if key in attr.lower():
                    val.set_text(sample)
                    break
        elif isinstance(val, Gtk.SpinButton):
            try:
                val.set_value(val.get_range()[0])
            except Exception:
                pass


def try_method(tab, method, timeout=0.3):
    try:
        fn = getattr(tab, method)
    except AttributeError:
        return "yok"
    try:
        fn()
    except Exception as e:
        return f"HATA: {type(e).__name__}: {e}"
    end = time.time() + timeout
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(0.03)
    return "OK"


for cat, tools in app.category_tools.items():
    for label, icon, tab in tools:
        if label in ("MITM", "Honeypot"):
            continue
        autofill(tab)
        for method in [x for x in dir(tab) if x.startswith("start_") and callable(getattr(tab, x))]:
            res = try_method(tab, method)
            if res != "OK":
                print(f"* {label:20s} {method:20s} {res}", flush=True)

print("=" * 60, flush=True)
print(f"THREAD HATALARI: {len(thread_errors)}", flush=True)
for e in thread_errors[:20]:
    print("  -", e, flush=True)
print("TAMAM", flush=True)
