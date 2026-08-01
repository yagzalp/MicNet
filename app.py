import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf
import os

from modules.subdomain import SubdomainTab
from modules.osint import OsintTab
from modules.wifi_scanner import WifiScannerTab
from modules.wifi_deauth import WifiDeauthTab
from modules.mitm import MITMTab
from modules.fake_mail import FakeMailTab
from modules.domain_analyzer import DomainAnalyzerTab
from modules.port_scanner import PortScannerTab
from modules.dns_lookup import DnsLookupTab
from modules.whois_lookup import WhoisTab
from modules.ip_geo import IpGeoTab
from modules.password_gen import PasswordGenTab
from modules.hash_tools import HashToolsTab
from modules.url_scanner import UrlScannerTab
from modules.mac_lookup import MacLookupTab
from modules.sql_injection import SqlInjectionTab
from modules.dir_buster import DirBusterTab
from modules.cms_detector import CmsDetectorTab
from modules.reverse_ip import ReverseIpTab
from modules.pwd_strength import PwdStrengthTab
from modules.email_breach import EmailBreachTab
from modules.arp_detector import ArpDetectorTab
from modules.network_mapper import NetworkMapperTab
from modules.settings_panel import SettingsTab
from modules.wifi_crack import WifiCrackTab
from modules.site_exploit import SiteExploitTab
from modules.ssl_checker import SslCheckerTab
from modules.http_headers import HttpHeadersTab
from modules.waf_detector import WafDetectorTab
from modules.cve_lookup import CveLookupTab
from modules.dns_zone import DnsZoneTab
from modules.robots_analyzer import RobotsAnalyzerTab
from modules.ip_reputation import IpReputationTab
from modules.metadata_forensics import MetadataTab
from modules.encoder_tools import EncoderToolsTab
from modules.subnet_calc import SubnetCalcTab
from modules.device_scanner import DeviceScannerTab
from datetime import datetime


class MicNetApp:
    def __init__(self):
        self.window = Gtk.Window(
            title="MicNet",
            default_width=1500,
            default_height=880,
        )
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)

        icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
        if os.path.exists(icon_path):
            self.window.set_icon_from_file(icon_path)

        css_data = b"""
        @define-color bg #0f0f1a;
        @define-color surface #1a1a2e;
        @define-color surface2 #252542;
        @define-color card #16162a;
        @define-color border #2a2a4a;
        @define-color text #e2e8f0;
        @define-color subtext #8899bb;
        @define-color muted #556688;
        @define-color primary #818cf8;
        @define-color primary2 #6366f1;
        @define-color accent #f472b6;
        @define-color success #34d399;
        @define-color warning #fbbf24;
        @define-color error #f87171;

        * { font-family: "Cantarell", "Noto Sans", sans-serif; }

        window { background-color: @bg; }

        headerbar {
            background: linear-gradient(to right, #0f0f1a, #1a1a2e);
            border: none;
            border-bottom: 1px solid @border;
            min-height: 44px;
            padding: 0 8px;
        }
        headerbar .title {
            font-weight: 800;
            font-size: 16px;
            color: @primary;
        }
        headerbar .subtitle {
            font-size: 11px;
            color: @muted;
        }

        notebook {
            background-color: @bg;
        }
        notebook header {
            background: #131326;
            border: none;
            border-bottom: 1px solid @border;
            padding: 2px 6px 0 6px;
        }
        notebook tab {
            background: transparent;
            border: none;
            padding: 5px 4px;
            margin: 0;
            border-radius: 8px 8px 0 0;
        }
        notebook tab:hover {
            background: rgba(129, 140, 248, 0.06);
        }
        notebook tab:checked {
            background: rgba(129, 140, 248, 0.1);
            border-bottom: 2px solid @primary;
        }
        notebook tab label {
            color: @muted;
            font-size: 9px;
            font-weight: 600;
        }
        notebook tab:checked label {
            color: @text;
        }
        notebook tab image {
            opacity: 0.5;
        }
        notebook tab:checked image {
            opacity: 1;
        }

        entry {
            background-color: @surface;
            color: @text;
            border: 1px solid @border;
            border-radius: 8px;
            padding: 9px 14px;
            font-size: 13px;
            caret-color: @primary;
        }
        entry:focus { border-color: @primary; box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.12); }
        entry:disabled { opacity: 0.5; }

        button {
            background-color: @surface2;
            color: @text;
            border: none;
            border-radius: 8px;
            padding: 9px 20px;
            font-size: 13px;
            font-weight: 600;
        }
        button:hover { background-color: #313155; }
        button:active { background: @primary2; }
        button:disabled { opacity: 0.35; }

        button.suggested-action {
            background: linear-gradient(135deg, @primary2, @primary);
            color: white;
            box-shadow: 0 3px 10px rgba(99, 102, 241, 0.25);
        }
        button.suggested-action:hover {
            background: linear-gradient(135deg, @primary, #a78bfa);
        }

        button.destructive-action {
            background: @error;
            color: white;
        }
        button.destructive-action:hover {
            background: #ef4444;
        }

        label { color: @subtext; font-size: 13px; }

        .title-label {
            font-size: 18px;
            font-weight: 700;
            color: @text;
            padding: 0;
        }

        .desc-label {
            font-size: 12px;
            color: @muted;
            padding: 2px 0 8px 0;
        }

        .card {
            background-color: @card;
            border: 1px solid @border;
            border-radius: 12px;
        }

        .card-header {
            color: @primary;
            font-weight: 700;
            font-size: 12px;
            padding: 0 4px 8px 4px;
        }

        .output-text {
            font-family: "Fira Code", "Cascadia Code", "JetBrains Mono", monospace;
            font-size: 12px;
            border-radius: 8px;
        }

        frame {
            border: 1px solid @border;
            border-radius: 12px;
            background: @card;
        }
        frame > label {
            color: @primary;
            font-weight: 700;
            font-size: 11px;
            padding: 0 12px;
        }

        scrolledwindow {
            background-color: #111122;
            border-radius: 8px;
        }
        textview { background: transparent; }
        textview text { background: transparent; }
        .output-text { background-color: #111122; }
        .output-text text { background-color: #111122; color: #a5b4fc; }

        treeview {
            background-color: #111122;
            color: #a5b4fc;
            font-family: monospace;
            font-size: 12px;
        }
        treeview:selected {
            background: rgba(129, 140, 248, 0.15);
            color: @text;
        }
        treeview header button {
            background-color: @surface;
            color: @muted;
            border: none;
            font-size: 11px;
            font-weight: 700;
        }
        treeview header button:hover { background-color: @surface2; }

        progressbar {
            background-color: @surface;
            border-radius: 8px;
            min-height: 8px;
        }
        progressbar progress {
            background: linear-gradient(90deg, @primary2, @accent);
            border-radius: 8px;
        }

        checkbutton { color: @subtext; }
        checkbutton check {
            background-color: @surface;
            border: 1px solid @border;
            border-radius: 5px;
            min-width: 18px;
            min-height: 18px;
        }
        checkbutton check:checked {
            background-color: @primary;
            border-color: @primary;
        }

        combobox {
            background-color: @surface;
            color: @text;
            border: 1px solid @border;
            border-radius: 8px;
        }
        combobox button {
            background: transparent;
            border: none;
            color: @text;
            padding: 9px 14px;
        }
        combobox button:hover { background: @surface2; }

        spinbutton {
            background-color: @surface;
            color: @text;
            border: 1px solid @border;
            border-radius: 8px;
        }

        scrollbar { background: transparent; }
        scrollbar slider {
            background-color: @border;
            border-radius: 6px;
            min-width: 6px;
        }
        scrollbar slider:hover { background-color: @primary; }

        separator {
            background-color: @border;
            min-height: 1px;
        }

        GtkSeparator { background-color: @border; }
        """

        style = Gtk.CssProvider()
        style.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.set_title("MicNet")
        header.set_subtitle("Siber Guvenlik Araci")

        if os.path.exists(icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 22, 22)
                img = Gtk.Image.new_from_pixbuf(pixbuf)
                header.pack_start(img)
            except Exception:
                pass

        vbox.pack_start(header, False, False, 0)

        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        notebook.set_scrollable(True)

        self.tabs_data = [
            ("Subdomain", "edit-find-symbolic", SubdomainTab()),
            ("OSINT", "system-search-symbolic", OsintTab()),
            ("Domain", "web-browser-symbolic", DomainAnalyzerTab()),
            ("WHOIS", "help-about-symbolic", WhoisTab()),
            ("DNS", "network-server-symbolic", DnsLookupTab()),
            ("ReverseIP", "network-server-symbolic", ReverseIpTab()),
            ("Konum", "find-location-symbolic", IpGeoTab()),
            ("Port", "network-transmit-symbolic", PortScannerTab()),
            ("URL", "web-browser-symbolic", UrlScannerTab()),
            ("CMS", "computer-symbolic", CmsDetectorTab()),
            ("SQLi", "dialog-warning-symbolic", SqlInjectionTab()),
            ("DirBust", "folder-symbolic", DirBusterTab()),
            ("Exploit", "dialog-warning-symbolic", SiteExploitTab()),
            ("MAC", "computer-symbolic", MacLookupTab()),
            ("Sifre", "dialog-password-symbolic", PasswordGenTab()),
            ("SifreTest", "dialog-password-symbolic", PwdStrengthTab()),
            ("Hash", "security-high-symbolic", HashToolsTab()),
            ("EPosta", "mail-send-symbolic", EmailBreachTab()),
            ("WiFi", "network-wireless-symbolic", WifiScannerTab()),
            ("WifiKir", "network-wireless-symbolic", WifiCrackTab()),
            ("Deauth", "network-offline-symbolic", WifiDeauthTab()),
            ("ARP", "network-transmit-symbolic", ArpDetectorTab()),
            ("Ag", "network-server-symbolic", NetworkMapperTab()),
            ("MITM", "media-record-symbolic", MITMTab()),
            ("Mail", "mail-send-symbolic", FakeMailTab()),
            ("SSL", "security-high-symbolic", SslCheckerTab()),
            ("Headers", "format-justify-fill-symbolic", HttpHeadersTab()),
            ("WAF", "security-medium-symbolic", WafDetectorTab()),
            ("CVE", "help-browser-symbolic", CveLookupTab()),
            ("DNSZone", "network-server-symbolic", DnsZoneTab()),
            ("Robots", "text-x-generic-symbolic", RobotsAnalyzerTab()),
            ("KaraListe", "system-lock-screen-symbolic", IpReputationTab()),
            ("Metadata", "image-x-generic-symbolic", MetadataTab()),
            ("Kodla", "accessories-text-editor-symbolic", EncoderToolsTab()),
            ("Subnet", "accessories-calculator-symbolic", SubnetCalcTab()),
            ("Cihazlar", "network-wireless-symbolic", DeviceScannerTab()),
            ("Ayarlar", "preferences-system-symbolic", SettingsTab()),
        ]

        for label, icon_name, tab in self.tabs_data:
            page_scroll = Gtk.ScrolledWindow()
            page_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            page_scroll.add(tab)

            tab_box = Gtk.Box(spacing=2)
            tab_box.set_hexpand(True)
            tab_box.set_halign(Gtk.Align.FILL)
            icon_w = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            icon_w.set_pixel_size(12)
            icon_w.set_halign(Gtk.Align.CENTER)
            tab_box.pack_start(icon_w, True, True, 0)
            lbl = Gtk.Label(label=label)
            lbl.get_style_context().add_class("tab-label")
            lbl.set_halign(Gtk.Align.CENTER)
            tab_box.pack_start(lbl, True, True, 0)
            tab_box.show_all()

            notebook.append_page(page_scroll, tab_box)

        vbox.pack_start(notebook, True, True, 0)

        toolbar = Gtk.Box(spacing=6)
        toolbar.set_size_request(-1, 28)
        toolbar.get_style_context().add_class("toolbar")
        toolbar.set_valign(Gtk.Align.CENTER)

        toolbar.pack_start(
            Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.MENU),
            False, False, 8
        )
        toolbar.pack_start(Gtk.Label(label="MicNet v2.0"), False, False, 4)

        toolbar.pack_end(Gtk.Label(label=f"{datetime.now().strftime('%H:%M')}"), False, False, 8)

        sep_l = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep_l.set_size_request(2, 18)
        toolbar.pack_end(sep_l, False, False, 2)

        export_btn = Gtk.Button(label="Ciktiyi Kaydet")
        export_btn.connect("clicked", lambda _: self.export_current())
        toolbar.pack_end(export_btn, False, False, 4)

        vbox.pack_end(toolbar, False, False, 0)

        self.notebook = notebook

        self.window.add(vbox)
        self.window.show_all()

    def export_current(self):
        page = self.notebook.get_current_page()
        scroll = self.notebook.get_nth_page(page)
        child = scroll.get_child() if scroll else None
        if not child:
            return
        textview = None
        for w in child.get_children() if hasattr(child, 'get_children') else []:
            if isinstance(w, Gtk.ScrolledWindow):
                tv = w.get_child()
                if isinstance(tv, Gtk.TextView):
                    textview = tv
                    break
            elif isinstance(w, Gtk.TextView):
                textview = w
                break
            elif hasattr(w, 'get_children'):
                for sw in w.get_children():
                    if isinstance(sw, Gtk.ScrolledWindow):
                        tv = sw.get_child()
                        if isinstance(tv, Gtk.TextView):
                            textview = tv
                            break
        if not textview:
            return
        buf = textview.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        if not text.strip():
            return

        dialog = Gtk.FileChooserDialog(
            title="Ciktiyi Kaydet",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT,
            ),
        )
        dialog.set_current_name("rapor.txt")

        filt_txt = Gtk.FileFilter()
        filt_txt.set_name("Metin dosyasi (*.txt)")
        filt_txt.add_pattern("*.txt")
        dialog.add_filter(filt_txt)

        filt_html = Gtk.FileFilter()
        filt_html.set_name("HTML (*.html)")
        filt_html.add_pattern("*.html")
        dialog.add_filter(filt_html)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            try:
                if path.endswith(".html"):
                    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>MicNet Raporu</title>
<style>
body {{ background: #0f0f1a; color: #e2e8f0; font-family: monospace; padding: 20px; }}
pre {{ background: #1a1a2e; padding: 16px; border-radius: 8px; }}
</style></head><body><pre>{text}</pre></body></html>"""
                    with open(path, "w") as f:
                        f.write(html)
                else:
                    with open(path, "w") as f:
                        f.write(text)
            except Exception as e:
                pass
        dialog.destroy()

    def run(self):
        Gtk.main()
