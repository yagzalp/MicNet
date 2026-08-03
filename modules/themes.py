import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class ThemesTab(Gtk.Box):
    def __init__(self, app, themes, current_theme):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)
        self.app = app
        self.themes = themes
        self.current_theme = current_theme

        title = Gtk.Label(label="Temalar")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Uygulama renk temasini secin. Secim aninda uygulanir ve kaydedilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(2)
        flow.set_homogeneous(True)
        flow.set_column_spacing(10)
        flow.set_row_spacing(10)

        self.buttons = {}
        for key, theme in themes.items():
            btn = self._make_theme_button(key, theme)
            self.buttons[key] = btn
            flow.add(btn)

        self.pack_start(flow, True, True, 0)

    def _make_theme_button(self, key, theme):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_size_request(220, 120)
        box.get_style_context().add_class("card")

        preview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        preview.set_size_request(-1, 56)
        for attr in ("bg", "surface", "surface2", "primary", "accent"):
            color = theme.get(attr, "#000000")
            cell = Gtk.Box()
            cell.set_hexpand(True)
            cell.override_background_color(Gtk.StateFlags.NORMAL, self._rgba(color))
            preview.pack_start(cell, True, True, 0)
        box.pack_start(preview, False, False, 0)

        name_lbl = Gtk.Label(label=theme["name"])
        name_lbl.get_style_context().add_class("card-header")
        box.pack_start(name_lbl, False, False, 0)

        btn = Gtk.Button()
        btn.add(box)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(f"'{theme['name']}' temasini uygula")
        btn.connect("clicked", lambda _: self.app.apply_theme(key))
        if key == self.current_theme:
            btn.get_style_context().add_class("suggested-action")
        return btn

    def _rgba(self, color):
        rgba = Gdk.RGBA()
        if rgba.parse(color):
            return rgba
        return Gdk.RGBA(0, 0, 0, 1)
