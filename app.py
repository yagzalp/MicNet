import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf
import os
import json

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
from modules.honeypot import HoneypotTab
from modules.xss_scanner import XssScannerTab
from modules.open_redirect import OpenRedirectTab
from modules.http_status import HttpStatusTab
from modules.s3_scanner import S3ScannerTab
from modules.hibp_check import HibpCheckTab
from modules.jwt_tool import JwtToolTab
from modules.tech_detect import TechDetectTab
from modules.link_extract import LinkExtractTab
from modules.email_extract import EmailExtractTab
from modules.sec_headers import SecHeadersTab
from modules.lfi_scanner import LfiScannerTab
from modules.cmd_injection import CmdInjectionTab
from modules.cors_scanner import CorsScannerTab
from modules.backup_finder import BackupFinderTab
from modules.file_hash import FileHashTab
from modules.sys_info import SysInfoTab
from modules.net_info import NetInfoTab
from modules.proc_list import ProcListTab
from modules.themes import ThemesTab
from datetime import datetime


THEMES = {
    "koyu": {
        "name": "Koyu",
        "bg": "#0b0b0b",
        "surface": "#151515",
        "surface2": "#202020",
        "card": "#111111",
        "border": "#2e2e2e",
        "text": "#f2f2f2",
        "subtext": "#a0a0a0",
        "muted": "#707070",
        "primary": "#ffffff",
        "primary2": "#d9d9d9",
        "accent": "#e5e5e5",
        "success": "#d4d4d4",
        "warning": "#b8b8b8",
        "error": "#9a9a9a",
        "grad1": "#0a0a0a",
        "grad2": "#151515",
        "focus-ring": "rgba(255, 255, 255, 0.12)",
        "btn-hover": "#2c2c2c",
        "suggest-hover": "#d9d9d9",
        "panel-bg": "#111111",
        "panel-text": "#ffffff",
        "selection-bg": "rgba(255, 255, 255, 0.18)",
        "progress-track": "#4a4a4a",
        "bar-bg": "#0e0e0e",
        "hover-bg": "rgba(255, 255, 255, 0.06)",
        "hover-text": "#c8c8c8",
        "active-bg": "rgba(255, 255, 255, 0.14)",
        "checked-bg": "#f2f2f2",
        "checked-fg": "#0b0b0b",
        "shadow": "rgba(0, 0, 0, 0.4)",
    },
    "acik": {
        "name": "Acik",
        "bg": "#f4f4f6",
        "surface": "#ffffff",
        "surface2": "#e8e8ec",
        "card": "#ffffff",
        "border": "#d0d0d6",
        "text": "#1a1a1e",
        "subtext": "#3a3a42",
        "muted": "#6b6b73",
        "primary": "#0a0a0c",
        "primary2": "#2a2a30",
        "accent": "#3f3f46",
        "success": "#2e7d32",
        "warning": "#9a6700",
        "error": "#c62828",
        "grad1": "#e8e8ec",
        "grad2": "#fafafb",
        "focus-ring": "rgba(0, 0, 0, 0.12)",
        "btn-hover": "#dcdce0",
        "suggest-hover": "#2a2a30",
        "panel-bg": "#ffffff",
        "panel-text": "#1a1a1e",
        "selection-bg": "rgba(0, 0, 0, 0.12)",
        "progress-track": "#bdbdc4",
        "bar-bg": "#ececef",
        "hover-bg": "rgba(0, 0, 0, 0.06)",
        "hover-text": "#4a4a52",
        "active-bg": "rgba(0, 0, 0, 0.14)",
        "checked-bg": "#1a1a1e",
        "checked-fg": "#ffffff",
        "shadow": "rgba(0, 0, 0, 0.25)",
    },
    "mavi": {
        "name": "Mavi",
        "bg": "#0a1220",
        "surface": "#122238",
        "surface2": "#1a3050",
        "card": "#0e1a2c",
        "border": "#2a4a72",
        "text": "#e8f0ff",
        "subtext": "#a0b8e0",
        "muted": "#6a84ac",
        "primary": "#7ab8ff",
        "primary2": "#4a90e0",
        "accent": "#90ccff",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "grad1": "#0a1628",
        "grad2": "#14264a",
        "focus-ring": "rgba(122, 184, 255, 0.30)",
        "btn-hover": "#1e3a60",
        "suggest-hover": "#4a90e0",
        "panel-bg": "#0e1a2c",
        "panel-text": "#e8f0ff",
        "selection-bg": "rgba(122, 184, 255, 0.25)",
        "progress-track": "#2a4a72",
        "bar-bg": "#0a1422",
        "hover-bg": "rgba(122, 184, 255, 0.10)",
        "hover-text": "#c8daf0",
        "active-bg": "rgba(122, 184, 255, 0.22)",
        "checked-bg": "#7ab8ff",
        "checked-fg": "#0a1220",
        "shadow": "rgba(0, 0, 0, 0.5)",
    },
    "yesil": {
        "name": "Yesil",
        "bg": "#0a1410",
        "surface": "#10241c",
        "surface2": "#163528",
        "card": "#0c1e16",
        "border": "#2a5a44",
        "text": "#e6ffe8",
        "subtext": "#a0e0b0",
        "muted": "#6aa07a",
        "primary": "#4ade80",
        "primary2": "#2eb060",
        "accent": "#86efac",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "grad1": "#0a1c14",
        "grad2": "#12302a",
        "focus-ring": "rgba(74, 222, 128, 0.30)",
        "btn-hover": "#1a4432",
        "suggest-hover": "#2eb060",
        "panel-bg": "#0c1e16",
        "panel-text": "#e6ffe8",
        "selection-bg": "rgba(74, 222, 128, 0.25)",
        "progress-track": "#2a5a44",
        "bar-bg": "#081412",
        "hover-bg": "rgba(74, 222, 128, 0.10)",
        "hover-text": "#c8f0d0",
        "active-bg": "rgba(74, 222, 128, 0.22)",
        "checked-bg": "#4ade80",
        "checked-fg": "#0a1410",
        "shadow": "rgba(0, 0, 0, 0.5)",
    },
    "mor": {
        "name": "Mor",
        "bg": "#140e22",
        "surface": "#1e1638",
        "surface2": "#2a1e4e",
        "card": "#181026",
        "border": "#44366e",
        "text": "#f0e8ff",
        "subtext": "#c0b0e0",
        "muted": "#8a78ac",
        "primary": "#c4a8ff",
        "primary2": "#9a72e0",
        "accent": "#d8c0ff",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "grad1": "#161026",
        "grad2": "#241a3e",
        "focus-ring": "rgba(196, 168, 255, 0.30)",
        "btn-hover": "#2c2048",
        "suggest-hover": "#9a72e0",
        "panel-bg": "#181026",
        "panel-text": "#f0e8ff",
        "selection-bg": "rgba(196, 168, 255, 0.25)",
        "progress-track": "#44366e",
        "bar-bg": "#120c1e",
        "hover-bg": "rgba(196, 168, 255, 0.10)",
        "hover-text": "#dcc8f0",
        "active-bg": "rgba(196, 168, 255, 0.22)",
        "checked-bg": "#c4a8ff",
        "checked-fg": "#140e22",
        "shadow": "rgba(0, 0, 0, 0.5)",
    },
    "kirmizi": {
        "name": "Kirmizi",
        "bg": "#1c0e0e",
        "surface": "#2e1616",
        "surface2": "#402020",
        "card": "#240e0e",
        "border": "#5a2e2e",
        "text": "#ffecec",
        "subtext": "#e0b0b0",
        "muted": "#a07070",
        "primary": "#ff8a8a",
        "primary2": "#e04a4a",
        "accent": "#ffb0b0",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#ff5c5c",
        "grad1": "#201010",
        "grad2": "#382222",
        "focus-ring": "rgba(255, 138, 138, 0.30)",
        "btn-hover": "#3c2222",
        "suggest-hover": "#e04a4a",
        "panel-bg": "#240e0e",
        "panel-text": "#ffecec",
        "selection-bg": "rgba(255, 138, 138, 0.25)",
        "progress-track": "#5a2e2e",
        "bar-bg": "#1a0c0c",
        "hover-bg": "rgba(255, 138, 138, 0.10)",
        "hover-text": "#f0c8c8",
        "active-bg": "rgba(255, 138, 138, 0.22)",
        "checked-bg": "#ff8a8a",
        "checked-fg": "#1c0e0e",
        "shadow": "rgba(0, 0, 0, 0.5)",
    },
}


class MicNetApp:
    def __init__(self):
        self.active_cat = None
        self.active_tool_btn = None
        self._switching = False
        self._fullscreen = False
        self._expanded = False
        self._cat_switch = False
        self.theme_name = self._load_theme()
        self._css_body = b""
        self._css_provider = None

        self.window = Gtk.Window(
            title="MicNet",
            default_width=1500,
            default_height=880,
        )
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("window-state-event", self._on_window_state)
        self.window.connect("key-press-event", self._on_key_press)

        icon_path = os.path.join(os.path.dirname(__file__), "icon.svg")
        if os.path.exists(icon_path):
            self.window.set_icon_from_file(icon_path)

        _CSS_BODY = b"""
        * { font-family: "Cantarell", "Noto Sans", sans-serif; }

        window { background-color: @bg; }

        headerbar {
            background: linear-gradient(to right, @grad1, @grad2);
            border: none;
            border-bottom: 1px solid @border;
            min-height: 44px;
            padding: 0 8px;
        }
        headerbar .title {
            font-weight: 800;
            font-size: 16px;
            color: @text;
            letter-spacing: 0.5px;
        }
        headerbar .subtitle {
            font-size: 11px;
            color: @muted;
        }

        entry {
            background-color: @surface;
            color: @text;
            border: 1px solid @border;
            border-radius: 8px;
            padding: 9px 14px;
            font-size: 13px;
            caret-color: @text;
            transition: border-color 150ms ease-out, background-color 150ms ease-out;
        }
        entry:focus { border-color: @text; box-shadow: 0 0 0 2px @focus-ring; }
        entry:disabled { opacity: 0.5; }

        button {
            background-color: @surface2;
            color: @text;
            border: none;
            border-radius: 8px;
            padding: 9px 20px;
            font-size: 13px;
            font-weight: 600;
            transition: background-color 150ms ease-out, color 150ms ease-out;
        }
        button:hover { background-color: @btn-hover; }
        button:active { background: @text; color: @bg; }
        button:disabled { opacity: 0.35; }

        button.suggested-action {
            background: @text;
            color: @bg;
            box-shadow: 0 2px 8px @shadow;
        }
        button.suggested-action:hover {
            background: @suggest-hover;
        }

        button.destructive-action {
            background: @error;
            color: @bg;
        }
        button.destructive-action:hover {
            background: @accent;
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
            color: @text;
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
            color: @text;
            font-weight: 700;
            font-size: 11px;
            padding: 0 12px;
        }

        scrolledwindow {
            background-color: @panel-bg;
            border-radius: 8px;
        }
        textview { background: transparent; }
        textview text { background: transparent; }
        .output-text { background-color: @panel-bg; }
        .output-text text { background-color: @panel-bg; color: @panel-text; }

        treeview {
            background-color: @panel-bg;
            color: @panel-text;
            font-family: monospace;
            font-size: 12px;
        }
        treeview:selected {
            background: @selection-bg;
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
            background: linear-gradient(90deg, @progress-track, @accent);
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
            background-color: @text;
            border-color: @text;
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
        scrollbar slider:hover { background-color: @muted; }

        separator {
            background-color: @border;
            min-height: 1px;
        }

        GtkSeparator { background-color: @border; }

        .statusbar {
            background-color: @bar-bg;
            border-top: 1px solid @border;
            padding: 4px 10px;
        }
        .statusbar label {
            color: @muted;
            font-size: 11px;
        }

        .cat-bar {
            background-color: @bar-bg;
            border-bottom: 1px solid @border;
            padding: 10px 12px 12px 12px;
        }
        .cat-btn {
            background: transparent;
            border: none;
            border-radius: 999px;
            padding: 8px 18px;
            color: @muted;
            font-size: 12px;
            font-weight: 700;
            transition: background-color 150ms ease-out, color 150ms ease-out;
        }
        .cat-btn:hover {
            background: @hover-bg;
            color: @hover-text;
        }
        .cat-btn:active {
            background: @active-bg;
        }
        .cat-btn:checked {
            background: @checked-bg;
            color: @checked-fg;
            box-shadow: 0 2px 10px @shadow;
        }

        .tool-bar {
            background-color: transparent;
            border-radius: 0;
            border: none;
        }
        .tool-bar-box {
            padding: 0 4px;
        }
        .tool-tab {
            background: transparent;
            border: none;
            border-radius: 9px 9px 0 0;
            padding: 8px 12px;
            margin: 0 1px;
            color: @muted;
            font-size: 11px;
            font-weight: 700;
            transition: background-color 150ms ease-out, color 150ms ease-out;
        }
        .tool-tab:hover {
            background: @hover-bg;
            color: @hover-text;
        }
        .tool-tab:active {
            background: @active-bg;
        }
        .tool-tab:checked {
            background: @checked-bg;
            color: @checked-fg;
            box-shadow: 0 2px 10px @shadow;
        }
        .tool-tab image { opacity: 0.55; }
        .tool-tab:hover image { opacity: 0.9; }
        .tool-tab:checked image { opacity: 1; }
        .tool-bar-compact .tool-tab {
            padding: 4px 4px;
            margin: 0;
        }
        .tool-bar-compact .tool-tab label {
            font-size: 11.5px;
        }
        """

        self._css_body = _CSS_BODY
        css_data = self._build_css()
        self._css_provider = Gtk.CssProvider()
        self._css_provider.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self._css_provider,
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

        self.category_tools = {
            "Kesif & Analiz": [
                ("Subdomain", "edit-find-symbolic", SubdomainTab()),
                ("OSINT", "system-search-symbolic", OsintTab()),
                ("Domain", "web-browser-symbolic", DomainAnalyzerTab()),
                ("WHOIS", "help-about-symbolic", WhoisTab()),
                ("DNS", "network-server-symbolic", DnsLookupTab()),
                ("Reverse IP", "network-server-symbolic", ReverseIpTab()),
                ("Konum", "find-location-symbolic", IpGeoTab()),
                ("Port", "network-transmit-symbolic", PortScannerTab()),
                ("URL", "web-browser-symbolic", UrlScannerTab()),
                ("CMS", "computer-symbolic", CmsDetectorTab()),
                ("DNSZone", "network-server-symbolic", DnsZoneTab()),
                ("Headers", "format-justify-fill-symbolic", HttpHeadersTab()),
                ("Robots", "text-x-generic-symbolic", RobotsAnalyzerTab()),
                ("Metadata", "image-x-generic-symbolic", MetadataTab()),
                ("Status", "network-transmit-receive-symbolic", HttpStatusTab()),
                ("S3", "folder-remote-symbolic", S3ScannerTab()),
                ("Tech", "computer-symbolic", TechDetectTab()),
                ("Links", "emblem-web-symbolic", LinkExtractTab()),
                ("Emails", "mail-send-symbolic", EmailExtractTab()),
            ],
            "Web Guvenligi": [
                ("SQLi", "dialog-warning-symbolic", SqlInjectionTab()),
                ("DirBust", "folder-symbolic", DirBusterTab()),
                ("Exploit", "dialog-warning-symbolic", SiteExploitTab()),
                ("SSL", "security-high-symbolic", SslCheckerTab()),
                ("WAF", "security-medium-symbolic", WafDetectorTab()),
                ("CVE", "help-browser-symbolic", CveLookupTab()),
                ("Blacklist", "system-lock-screen-symbolic", IpReputationTab()),
                ("EPosta", "mail-send-symbolic", EmailBreachTab()),
                ("XSS", "dialog-warning-symbolic", XssScannerTab()),
                ("Redirect", "go-next-symbolic", OpenRedirectTab()),
                ("LFI", "folder-drag-accept-symbolic", LfiScannerTab()),
                ("Komut", "utilities-terminal-symbolic", CmdInjectionTab()),
                ("CORS", "emblem-shared-symbolic", CorsScannerTab()),
                ("Yedek", "document-save-as-symbolic", BackupFinderTab()),
                ("SHead", "security-high-symbolic", SecHeadersTab()),
            ],
            "Ag & WiFi": [
                ("WiFi", "network-wireless-symbolic", WifiScannerTab()),
                ("WiFi Crack", "network-wireless-symbolic", WifiCrackTab()),
                ("Deauth", "network-offline-symbolic", WifiDeauthTab()),
                ("ARP", "network-transmit-symbolic", ArpDetectorTab()),
                ("Ag", "network-server-symbolic", NetworkMapperTab()),
                ("MITM", "media-record-symbolic", MITMTab()),
                ("Honeypot", "utilities-system-monitor-symbolic", HoneypotTab()),
                ("Cihazlar", "network-wireless-symbolic", DeviceScannerTab()),
            ],
            "Arac Kutusu": [
                ("Sifre", "dialog-password-symbolic", PasswordGenTab()),
                ("Password Test", "dialog-password-symbolic", PwdStrengthTab()),
                ("Hash", "security-high-symbolic", HashToolsTab()),
                ("MAC", "computer-symbolic", MacLookupTab()),
                ("Kodla", "accessories-text-editor-symbolic", EncoderToolsTab()),
                ("Subnet", "accessories-calculator-symbolic", SubnetCalcTab()),
                ("Mail", "mail-send-symbolic", FakeMailTab()),
                ("Password Leak", "security-low-symbolic", HibpCheckTab()),
                ("JWT", "document-properties-symbolic", JwtToolTab()),
                ("File Hash", "edit-find-symbolic", FileHashTab()),
            ],
            "Sistem": [
                ("Ayarlar", "preferences-system-symbolic", SettingsTab()),
                ("Sistem Bilgi", "computer-symbolic", SysInfoTab()),
                ("Ag Bilgi", "network-server-symbolic", NetInfoTab()),
                ("Surecler", "system-run-symbolic", ProcListTab()),
                ("Temalar", "preferences-desktop-theme-symbolic", ThemesTab(self, THEMES, self.theme_name)),
            ],
        }

        self.stack = Gtk.Stack()
        self.stack.set_homogeneous(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(350)

        for cat_name, tools in self.category_tools.items():
            for label, _icon_name, tab in tools:
                page_scroll = Gtk.ScrolledWindow()
                page_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                page_scroll.add(tab)
                self.stack.add_named(page_scroll, label)

        self.cat_bar = Gtk.Box(spacing=6)
        self.cat_bar.get_style_context().add_class("cat-bar")
        self.cat_bar.set_halign(Gtk.Align.CENTER)
        self.cat_bar.set_hexpand(True)

        self.cat_buttons = []
        for cat_name in self.category_tools.keys():
            btn = self._make_cat_btn(cat_name)
            btn.connect("clicked", self._on_cat_clicked, cat_name)
            self.cat_bar.pack_start(btn, False, False, 0)
            self.cat_buttons.append((btn, cat_name))

        vbox.pack_start(self.cat_bar, False, False, 0)

        tool_scroll = Gtk.ScrolledWindow()
        tool_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        tool_scroll.get_style_context().add_class("tool-bar")
        tool_scroll.set_overlay_scrolling(True)
        tool_scroll.set_vexpand(False)

        self.tool_bar = Gtk.Box(spacing=2)
        self.tool_bar.get_style_context().add_class("tool-bar-box")
        self.tool_bar.set_valign(Gtk.Align.CENTER)
        self.tool_scroll = tool_scroll
        tool_scroll.add(self.tool_bar)
        vbox.pack_start(tool_scroll, False, False, 0)
        vbox.pack_start(self.stack, True, True, 0)

        statusbar = Gtk.Box(spacing=8)
        statusbar.get_style_context().add_class("statusbar")
        statusbar.set_valign(Gtk.Align.CENTER)

        statusbar.pack_start(
            Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.MENU),
            False, False, 4
        )
        statusbar.pack_start(Gtk.Label(label="MicNet v2.0"), False, False, 0)

        statusbar.pack_end(Gtk.Label(label=f"{datetime.now().strftime('%H:%M')}"), False, False, 0)

        sep_l = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep_l.set_size_request(2, 18)
        statusbar.pack_end(sep_l, False, False, 2)

        export_btn = Gtk.Button(label="Ciktiyi Kaydet")
        export_btn.connect("clicked", lambda _: self.export_current())
        statusbar.pack_end(export_btn, False, False, 0)

        vbox.pack_end(statusbar, False, False, 0)

        self.window.add(vbox)
        self.window.show_all()
        self.window.maximize()

        first_btn, first_cat = self.cat_buttons[0]
        self.active_cat = first_cat
        first_btn.set_active(True)
        self._populate_tools(first_cat)

    def _make_cat_btn(self, text):
        btn = Gtk.ToggleButton(label=text)
        btn.get_style_context().add_class("cat-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_can_focus(False)
        return btn

    def _build_css(self):
        theme = THEMES.get(self.theme_name, THEMES["koyu"])
        parts = [f"        @define-color {k} {v};" for k, v in theme.items() if k != "name"]
        header = "\n".join(parts).encode()
        return header + b"\n" + self._css_body

    def _load_theme(self):
        try:
            path = os.path.expanduser("~/.config/micnet/config.json")
            with open(path) as f:
                cfg = json.load(f)
            name = cfg.get("theme", "koyu")
            if name in THEMES:
                return name
        except Exception:
            pass
        return "koyu"

    def _save_theme(self):
        try:
            os.makedirs(os.path.expanduser("~/.config/micnet"), exist_ok=True)
            path = os.path.expanduser("~/.config/micnet/config.json")
            cfg = {}
            try:
                with open(path) as f:
                    cfg = json.load(f)
            except Exception:
                pass
            cfg["theme"] = self.theme_name
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def apply_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        self._save_theme()
        if self._css_provider is not None:
            self._css_provider.load_from_data(self._build_css())

    def _make_tool_tab(self, text, icon_name):
        btn = Gtk.ToggleButton()
        btn.get_style_context().add_class("tool-tab")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_can_focus(False)

        compact = self._expanded
        box = Gtk.Box(spacing=1 if compact else 6)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        icon.set_pixel_size(14 if compact else 18)
        lbl = Gtk.Label(label=text)
        box.pack_start(icon, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        btn.add(box)
        btn.set_tooltip_text(text)
        return btn

    def _on_cat_clicked(self, btn, cat_name):
        if self._switching:
            return
        if self.active_cat == cat_name:
            btn.set_active(True)
            return
        self._switching = True
        try:
            self.active_cat = cat_name
            for b, n in self.cat_buttons:
                b.set_active(n == cat_name)
            self._populate_tools(cat_name)
        finally:
            self._switching = False

    def _populate_tools(self, cat_name):
        for child in self.tool_bar.get_children():
            self.tool_bar.remove(child)

        self.tool_buttons = []
        for label, icon_name, _tab in self.category_tools[cat_name]:
            btn = self._make_tool_tab(label, icon_name)
            btn.connect("clicked", self._on_tool_clicked, label)
            self.tool_bar.pack_start(btn, False, False, 0)
            self.tool_buttons.append((btn, label))

        self.tool_bar.show_all()

        self._apply_expanded_layout()

        if self.tool_buttons:
            btn, label = self.tool_buttons[0]
            self._cat_switch = True
            self._set_tool_active(btn, label)

    def _set_tool_active(self, btn, label):
        self._switching = True
        try:
            btn.set_active(True)
            if self.active_tool_btn and self.active_tool_btn is not btn:
                self.active_tool_btn.set_active(False)
            self.active_tool_btn = btn
            if self._cat_switch:
                self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
                self._cat_switch = False
            elif self.stack.get_visible_child_name() != label:
                self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            if self.stack.get_visible_child_name() != label:
                self.stack.set_visible_child_name(label)
        finally:
            self._switching = False

    def _on_tool_clicked(self, btn, label):
        if self._switching:
            return
        self._set_tool_active(btn, label)

    def _toggle_fullscreen(self, _=None):
        if self._fullscreen:
            self.window.unfullscreen()
        else:
            self.window.fullscreen()

    def _on_key_press(self, win, event):
        if event.keyval == Gdk.KEY_F11:
            self._toggle_fullscreen()
            return True
        return False

    def _on_window_state(self, win, event):
        fs = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)
        maxi = bool(event.new_window_state & Gdk.WindowState.MAXIMIZED)
        if fs != self._fullscreen:
            self._fullscreen = fs
        expanded = fs or maxi
        if expanded != self._expanded:
            self._expanded = expanded
            self._apply_expanded_layout()
        return False

    def _apply_expanded_layout(self):
        fs = self._expanded
        self.cat_bar.set_halign(Gtk.Align.FILL if fs else Gtk.Align.CENTER)
        self.cat_bar.set_homogeneous(fs)
        self.tool_bar.set_homogeneous(fs)
        self.tool_bar.set_hexpand(fs)
        self.tool_bar.set_spacing(1 if fs else 2)
        if fs:
            self.tool_scroll.get_style_context().add_class("tool-bar-compact")
        else:
            self.tool_scroll.get_style_context().remove_class("tool-bar-compact")
        for btn, _label in self.cat_buttons:
            self.cat_bar.set_child_packing(btn, fs, True, 0, Gtk.PackType.START)
        for btn, _label in getattr(self, "tool_buttons", []):
            self.tool_bar.set_child_packing(btn, fs, True, 0, Gtk.PackType.START)

    def _find_textview(self, widget):
        if isinstance(widget, Gtk.TextView):
            return widget
        if hasattr(widget, "get_children"):
            for child in widget.get_children():
                result = self._find_textview(child)
                if result:
                    return result
        return None

    def export_current(self):
        page = self.stack.get_visible_child()
        if not page:
            return
        textview = self._find_textview(page)
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
body {{ background: #0b0b0b; color: #f2f2f2; font-family: monospace; padding: 20px; }}
pre {{ background: #151515; padding: 16px; border-radius: 8px; }}
</style></head><body><pre>{text}</pre></body></html>"""
                    with open(path, "w") as f:
                        f.write(html)
                else:
                    with open(path, "w") as f:
                        f.write(text)
            except Exception:
                pass
        dialog.destroy()

    def run(self):
        Gtk.main()
