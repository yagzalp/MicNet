#!/bin/bash
cd "$(dirname "$0")"

if ! python3 -c "import gi" 2>/dev/null; then
    zenity --error --text="PyGObject (python3-gi) kurulu degil.\n\nKurulum:\nsudo apt install python3-gi gir1.2-gtk-3.0" 2>/dev/null || echo "python3-gi kurulu degil"
    exit 1
fi

for m in requests dns pyperclip scapy; do
    if ! python3 -c "import $m" 2>/dev/null; then
        echo "Eksik: $m -> pip install -r requirements.txt"
        pip3 install -r requirements.txt --user 2>/dev/null || zenity --error --text="Eksik paket: $m\npip install -r requirements.txt" 2>/dev/null
    fi
done

python3 main.py
