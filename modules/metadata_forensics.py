import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import os
import struct
from datetime import datetime


class MetadataTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Dosya Metadata & Forensics")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir dosyanin gizli metadata bilgilerini cikarir: EXIF (kamera modeli, tarih, GPS), dosya tipi, icerikteki sifre/anahtar benzeri izler. Adli bilişim ve gizlilik analizi icin.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Dosya")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.file_entry = Gtk.Entry(placeholder_text="Dosya yolu secin...")
        self.file_entry.set_size_request(380, 30)
        hbox.pack_start(self.file_entry, False, False, 0)
        browse_btn = Gtk.Button(label="Gez")
        browse_btn.connect("clicked", lambda _: self.browse())
        hbox.pack_start(browse_btn, False, False, 0)
        self.analyze_btn = Gtk.Button(label="Analiz Et")
        self.analyze_btn.connect("clicked", lambda _: self.start_analyze())
        self.analyze_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.analyze_btn, False, False, 0)
        input_box.pack_start(hbox, False, False, 0)

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

        self.running = False

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def browse(self):
        dialog = Gtk.FileChooserDialog(
            title="Dosya Sec",
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT),
        )
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self.file_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def start_analyze(self):
        path = self.file_entry.get_text().strip()
        if not path or not os.path.exists(path):
            self.status_label.set_text("Gecerli bir dosya yolu girin")
            return
        if self.running:
            return
        self.running = True
        self.analyze_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Analiz ediliyor...")
        thread = threading.Thread(target=self.analyze, args=(path,), daemon=True)
        thread.start()

    def detect_type(self, data):
        if data[:3] == b"\xff\xd8\xff":
            return "JPEG image"
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "PNG image"
        if data[:4] == b"GIF8":
            return "GIF image"
        if data[:5] == b"%PDF-":
            return "PDF document"
        if data[:2] == b"PK":
            return "ZIP/Office document (OLE)"
        if data[:4] == b"\x7fELF":
            return "ELF executable"
        if data[:4] == b"\x00asm":
            return "WebAssembly"
        if data[:4] == b"II*\x00" or data[:4] == b"MM\x00*":
            return "TIFF image"
        if data[:3] == b"\xef\xbb\xbf":
            return "UTF-8 text (BOM)"
        return "Bilinmeyen / metin"

    def parse_exif(self, data):
        info = {}
        if data[:2] != b"\xff\xd8":
            return info
        pos = 2
        while pos < len(data) - 8:
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xD8, 0xD9):
                pos += 2
                continue
            if marker == 0x01:
                pos += 2
                continue
            if marker in (0xDA,):
                break
            seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            if marker == 0xE1 and data[pos + 4:pos + 10] == b"Exif\x00\x00":
                return self._parse_tiff(data[pos + 10:pos + 2 + seg_len])
            pos += 2 + seg_len
        return info

    def _read_type(self, buf, offset, ttype, count):
        size_map = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}
        endian = "<" if self._le else ">"
        nbytes = size_map.get(ttype, 1) * count
        if nbytes <= 4:
            raw = buf[offset:offset + 4]
        else:
            addr = struct.unpack(endian + "I", buf[offset:offset + 4])[0]
            raw = buf[addr:addr + nbytes]
        try:
            if ttype == 2:
                return raw.split(b"\x00")[0].decode("utf-8", errors="replace")
            if ttype == 3:
                vals = struct.unpack(endian + ("H" * count), raw[:count * 2])
                return vals[0] if count == 1 else vals
            if ttype == 4:
                vals = struct.unpack(endian + ("I" * count), raw[:count * 4])
                return vals[0] if count == 1 else vals
            if ttype == 5:
                vals = []
                for i in range(count):
                    n, d = struct.unpack(endian + "II", raw[i * 8:i * 8 + 8])
                    vals.append(n / d if d else 0)
                return vals[0] if count == 1 else vals
            if ttype == 1:
                vals = struct.unpack(endian + ("B" * count), raw[:count])
                return vals[0] if count == 1 else vals
        except Exception:
            pass
        return None

    def _parse_tiff(self, tiff):
        info = {}
        try:
            if tiff[:2] == b"II":
                self._le = True
            elif tiff[:2] == b"MM":
                self._le = False
            else:
                return info
            endian = "<" if self._le else ">"
            ifd0_off = struct.unpack(endian + "I", tiff[4:8])[0]
            if ifd0_off + 2 > len(tiff):
                return info

            exif_ifd_off = None
            gps_ifd_off = None
            ifd = ifd0_off
            for _ in range(3):
                if ifd + 2 > len(tiff):
                    break
                n = struct.unpack(endian + "H", tiff[ifd:ifd + 2])[0]
                for i in range(n):
                    e = ifd + 2 + i * 12
                    if e + 12 > len(tiff):
                        break
                    tag, ttype, count = struct.unpack(endian + "HHI", tiff[e:e + 8])
                    val = self._read_type(tiff, e + 8, ttype, count)
                    if tag == 0x010F:
                        info["Make"] = val
                    elif tag == 0x0110:
                        info["Model"] = val
                    elif tag == 0x0131:
                        info["Software"] = val
                    elif tag == 0x0132:
                        info["DateTime"] = val
                    elif tag == 0x010E:
                        info["ImageDescription"] = val
                    elif tag == 0x8769:
                        exif_ifd_off = val
                    elif tag == 0x8825:
                        gps_ifd_off = val
                next_off = ifd + 2 + n * 12
                if next_off + 4 > len(tiff):
                    break
                nxt = struct.unpack(endian + "I", tiff[next_off:next_off + 4])[0]
                if nxt == 0:
                    break
                ifd = nxt

            if exif_ifd_off:
                try:
                    eifd = exif_ifd_off
                    n = struct.unpack(endian + "H", tiff[eifd:eifd + 2])[0]
                    for i in range(n):
                        e = eifd + 2 + i * 12
                        if e + 12 > len(tiff):
                            break
                        tag, ttype, count = struct.unpack(endian + "HHI", tiff[e:e + 8])
                        val = self._read_type(tiff, e + 8, ttype, count)
                        if tag == 0x9003:
                            info["DateTimeOriginal"] = val
                        elif tag == 0x9004:
                            info["DateTimeDigitized"] = val
                        elif tag == 0x8827:
                            info["ISO"] = val
                        elif tag == 0x829A:
                            info["ExposureTime"] = val
                        elif tag == 0x829D:
                            info["FNumber"] = val
                        elif tag == 0xA002:
                            info["PixelWidth"] = val
                        elif tag == 0xA003:
                            info["PixelHeight"] = val
                except Exception:
                    pass

            if gps_ifd_off:
                try:
                    gifd = gps_ifd_off
                    n = struct.unpack(endian + "H", tiff[gifd:gifd + 2])[0]
                    gps = {}
                    for i in range(n):
                        e = gifd + 2 + i * 12
                        if e + 12 > len(tiff):
                            break
                        tag, ttype, count = struct.unpack(endian + "HHI", tiff[e:e + 8])
                        val = self._read_type(tiff, e + 8, ttype, count)
                        gps[tag] = val
                    if 0x0002 in gps and 0x0004 in gps:
                        lat = gps[0x0002]
                        lon = gps[0x0004]
                        lat_ref = gps.get(0x0001, "N")
                        lon_ref = gps.get(0x0003, "E")
                        if isinstance(lat, (list, tuple)) and isinstance(lon, (list, tuple)):
                            def to_dec(vals):
                                if len(vals) >= 3:
                                    return vals[0] + vals[1] / 60 + vals[2] / 3600
                                return None
                            lat_d = to_dec(lat)
                            lon_d = to_dec(lon)
                            if lat_d is not None and lon_d is not None:
                                if str(lat_ref).upper() == "S":
                                    lat_d = -lat_d
                                if str(lon_ref).upper() == "W":
                                    lon_d = -lon_d
                                info["GPS"] = f"{lat_d:.6f}, {lon_d:.6f}"
                                info["GPSHref"] = f"https://maps.google.com/maps?q={lat_d},{lon_d}"
                except Exception:
                    pass
        except Exception:
            pass
        return info

    def parse_png(self, data):
        info = {}
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return info
        pos = 8
        while pos + 8 <= len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            body = data[pos + 8:pos + 8 + length]
            if ctype == b"IHDR":
                w, h = struct.unpack(">II", body[:8])
                info["Width"] = w
                info["Height"] = h
            elif ctype == b"tEXt":
                try:
                    key, _, value = body.partition(b"\x00")
                    info[key.decode("latin-1")] = value.decode("latin-1", errors="replace")
                except Exception:
                    pass
            elif ctype == b"IEND":
                break
            pos += 12 + length
        return info

    def parse_pdf(self, data):
        info = {}
        for marker in (b"/Producer", b"/Creator", b"/CreationDate"):
            idx = data.find(marker)
            if idx >= 0:
                rest = data[idx:idx + 200]
                val = rest.split(b"/")[1].split(b">")[0].strip(b"()").decode("latin-1", errors="replace")[:80]
                info[marker.decode().lstrip("/")] = val
        return info

    def analyze(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read(2000000)
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Dosya okunamadi: {e}")
            GLib.idle_add(self.finish_analyze)
            return

        st = os.stat(path)
        GLib.idle_add(self.log, f"[*] Dosya: {path}")
        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== TEMEL BILGILER ===")
        GLib.idle_add(self.log, f"  Boyut: {st.st_size:,} bayt ({st.st_size/1024:.1f} KB)")
        GLib.idle_add(self.log, f"  Degistirilme: {datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        GLib.idle_add(self.log, f"  Olusturulma: {datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
        GLib.idle_add(self.log, f"  Tip (magic bytes): {self.detect_type(data)}")
        GLib.idle_add(self.log, "")

        exif = self.parse_exif(data)
        png = self.parse_png(data)
        pdf = self.parse_pdf(data)

        GLib.idle_add(self.log, "=== EXIF / METADATA ===")
        merged = {}
        merged.update(exif)
        if png:
            merged["PNG"] = png
        if pdf:
            merged["PDF"] = pdf
        if not merged:
            GLib.idle_add(self.log, "  [-] EXIF/metadata bulunamadi (temiz dosya)")
        else:
            for k, v in merged.items():
                if isinstance(v, dict):
                    GLib.idle_add(self.log, f"  [{k}]")
                    for k2, v2 in v.items():
                        GLib.idle_add(self.log, f"    {k2}: {v2}")
                else:
                    GLib.idle_add(self.log, f"  {k}: {v}")

        if "GPS" in exif:
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "=== KONUM BILGISI ===")
            GLib.idle_add(self.log, f"  [!] GPS koordinati: {exif['GPS']}")
            GLib.idle_add(self.log, f"      {exif.get('GPSHref','')}")
            GLib.idle_add(self.log, "      Kamera cihaz konumunu kaydetmis! Dosya paylasmadan once temizlenmeli.")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== GIZLI IZLER (strings) ===")
        interesting = [b"password", b"passwd", b"secret", b"api_key", b"apikey",
                       b"token", b"private", b"BEGIN RSA", b"BEGIN PRIVATE",
                       b"BEGIN CERTIFICATE", b"smtp", b"root:", b"username"]
        found_any = False
        lower = data.lower()
        for kw in interesting:
            idx = 0
            while True:
                idx = lower.find(kw, idx)
                if idx < 0:
                    break
                snippet = data[max(0, idx - 20):idx + 60]
                printable = "".join(chr(b) if 32 <= b < 127 else "." for b in snippet)
                GLib.idle_add(self.log, f"  [!] '{kw.decode()}': ...{printable}...")
                found_any = True
                idx += len(kw)
                if idx > len(data):
                    break
        if not found_any:
            GLib.idle_add(self.log, "  [+] Dikkat cekici gizli iz bulunamadi")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== GIZLILIK TAVSIYESI ===")
        if exif or found_any:
            GLib.idle_add(self.log, "  [*] Metadata temizleme: exiftool -all= dosya.jpg")
        else:
            GLib.idle_add(self.log, "  [*] Dosya genel olarak temiz gorunuyor")

        GLib.idle_add(self.finish_analyze)

    def finish_analyze(self):
        self.running = False
        self.analyze_btn.set_sensitive(True)
        self.status_label.set_text("Analiz tamamlandi")
