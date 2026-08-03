import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import json
import base64
import binascii
import datetime


class JwtToolTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="JWT Cozumleyici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="JSON Web Token (JWT) header ve payload kismini base64url cozumler. Kullanilan imza algoritmasini, tokenin gecerlilik suresini ve 'none' algoritma riskini gosterir. Sifrelemeyi KIRMAZ, yalnizca cozumler.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="JWT Token")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        self.entry = Gtk.Entry(placeholder_text="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...")
        self.entry.set_size_request(-1, 30)
        self.entry.set_hexpand(True)
        self.entry.connect("activate", lambda _: self.decode())
        input_box.pack_start(self.entry, False, False, 0)

        self.decode_btn = Gtk.Button(label="Cozumle")
        self.decode_btn.connect("clicked", lambda _: self.decode())
        self.decode_btn.get_style_context().add_class("suggested-action")
        self.decode_btn.set_halign(Gtk.Align.CENTER)
        input_box.pack_start(self.decode_btn, False, False, 0)

        frame.add(input_box)
        self.pack_start(frame, False, False, 0)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textview.get_style_context().add_class("output-text")
        self.textbuffer = self.textview.get_buffer()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.textview)
        self.pack_start(sw, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def b64url(self, part):
        pad = "=" * (-len(part) % 4)
        return base64.urlsafe_b64decode(part + pad)

    def decode(self):
        token = self.entry.get_text().strip()
        self.textbuffer.set_text("")
        if not token:
            self.status_label.set_text("JWT girin")
            return
        parts = token.split(".")
        if len(parts) != 3:
            self.status_label.set_text("Gecersiz JWT - 3 parcadan olusmali")
            return
        self.status_label.set_text("Cozumlendi")
        try:
            header = json.loads(self.b64url(parts[0]))
            self.log("[Header]")
            self.log(json.dumps(header, indent=2, ensure_ascii=False))
        except (binascii.Error, ValueError, json.JSONDecodeError) as e:
            self.log("[-] Header cozumlenemedi: " + str(e))
            header = {}
        self.log("")
        try:
            payload = json.loads(self.b64url(parts[1]))
            self.log("[Payload]")
            self.log(json.dumps(payload, indent=2, ensure_ascii=False))
        except (binascii.Error, ValueError, json.JSONDecodeError) as e:
            self.log("[-] Payload cozumlenemedi: " + str(e))
            payload = {}

        alg = header.get("alg", "bilinmiyor")
        self.log("")
        if alg.lower() == "none":
            self.log("[!] RISK: 'none' algoritmasi! Imza dogrulamasi yok, token sahtelenebilir.")
        elif alg in ("HS256", "HS384", "HS512"):
            self.log(f"[*] Algoritma: {alg} (HMAC) - imza gizli anahtara bagli")
        elif alg in ("RS256", "RS384", "RS512"):
            self.log(f"[*] Algoritma: {alg} (RSA) - imza acik/gizli anahtar ikilisine bagli")
        elif alg in ("ES256", "ES384", "ES512"):
            self.log(f"[*] Algoritma: {alg} (ECDSA)")
        else:
            self.log(f"[*] Algoritma: {alg}")

        exp = payload.get("exp")
        if exp is not None:
            exp_dt = datetime.datetime.fromtimestamp(int(exp))
            now = datetime.datetime.now()
            if exp_dt > now:
                self.log(f"[*] Gecerlilik: {exp_dt.strftime('%Y-%m-%d %H:%M:%S')} (suresi dolmamis)")
            else:
                self.log(f"[!] Gecerlilik: {exp_dt.strftime('%Y-%m-%d %H:%M:%S')} (SURESI DOLMUS)")

        iat = payload.get("iat")
        if iat is not None:
            iat_dt = datetime.datetime.fromtimestamp(int(iat))
            self.log(f"[*] Olusturulma: {iat_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        if alg.lower() == "none":
            self.status_label.set_text("Riskli token: 'none' algoritmasi tespit edildi")
