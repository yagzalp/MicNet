#!/bin/bash
# =============================================================
# MicNet - Masaüstü Kısayolu Kurulum Scripti
# =============================================================
set -e

# Bu script'in bulunduğu dizini (proje klasörünü) otomatik algılar
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$PROJECT_DIR/micnet.desktop"
APPS_DIR="$HOME/.local/share/applications"

echo "MicNet kurulum dizini: $PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/run.sh" ]; then
    echo "HATA: run.sh bulunamadı. Bu scripti proje klasörünün içinden çalıştırın."
    exit 1
fi

chmod +x "$PROJECT_DIR/run.sh"

# .desktop dosyasındaki yolları bu bilgisayara göre otomatik günceller
mkdir -p "$APPS_DIR"
sed \
    -e "s|^Exec=.*|Exec=bash $PROJECT_DIR/run.sh|" \
    -e "s|^Icon=.*|Icon=$PROJECT_DIR/icon.svg|" \
    "$DESKTOP_FILE" > "$APPS_DIR/micnet.desktop"

chmod +x "$APPS_DIR/micnet.desktop"

# Masaüstüne de kısayol oluştur (varsa)
if [ -d "$HOME/Desktop" ]; then
    cp "$APPS_DIR/micnet.desktop" "$HOME/Desktop/micnet.desktop"
    chmod +x "$HOME/Desktop/micnet.desktop"
    # GNOME/Nautilus "güvenilir" işareti (varsa gio kullanılır)
    command -v gio >/dev/null 2>&1 && gio set "$HOME/Desktop/micnet.desktop" metadata::trusted true 2>/dev/null || true
fi

# Uygulama menüsü veritabanını günceller
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo ""
echo "✅ Kurulum tamamlandı!"
echo "   - Uygulama menüsünde 'MicNet' aratabilirsiniz."
echo "   - Masaüstünüzde kısayol oluşturuldu (varsa)."
