#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal
Criador: @tadalas no Discord
"""

import sys
import os
import time
import socket
import struct
import json
import glob
import subprocess
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple

VERSION = "1.2.0"
CREATOR = "@tadalas"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".livefreebrasil_cache.json")

# Configura encoding de saída para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Pool de nós rápidos internacionais pré-validados (Não-BR) para boot instantâneo (< 0.5s)
FAST_RELAYS = [
    ("socks5", "127.0.0.1", 9050, "Tor Local"),
    ("socks5", "127.0.0.1", 9150, "Tor Local"),
    ("socks5", "144.172.101.188", 1080, "Estados Unidos"),
    ("socks5", "5.249.165.195", 20000, "Estados Unidos"),
    ("socks5", "192.252.208.70", 14282, "Estados Unidos"),
    ("socks5", "198.23.239.134", 6543, "Estados Unidos"),
    ("socks5", "207.244.217.165", 6712, "Estados Unidos"),
    ("socks5", "68.71.249.152", 4145, "Canadá"),
    ("socks5", "98.188.47.112", 4145, "Estados Unidos"),
    ("http", "45.66.249.187", 8181, "Holanda"),
    ("http", "204.76.203.9", 3128, "Estados Unidos"),
    ("http", "159.65.77.156", 3128, "Alemanha"),
    ("http", "165.154.226.96", 80, "Singapura"),
    ("http", "38.180.9.158", 4422, "Reino Unido"),
    ("http", "198.199.86.11", 8080, "Estados Unidos"),
]

# Cores ANSI
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def print_banner():
    banner = rf"""
{Color.GREEN}{Color.BOLD}==================================================================
  _     _           _____              ____                 _ _ 
 | |   (_)_   _____|  ___| __ ___  ___| __ ) _ __ __ _ ___ (_) |
 | |   | \ \ / / _ \ |_ | '__/ _ \/ _ \  _ \| '__/ _` / __|| | |
 | |___| |\ V /  __/  _|| | |  __/  __/ |_) | | | (_| \__ \| | |
 |_____|_| \_/ \___|_|  |_|  \___|\___|____/|_|  \__,_|___/|_|_|
                                                                
{Color.WHITE}{Color.BOLD}  LiveFreeBrasil — Desbloqueio de Tela & Câmera no Discord v{VERSION}
{Color.CYAN}  Criado por: {Color.WHITE}{CREATOR} {Color.CYAN}no Discord
{Color.GREEN}=================================================================={Color.RESET}
"""
    print(banner, flush=True)

def log_info(msg: str):
    print(f"{Color.BLUE}[*]{Color.RESET} {msg}", flush=True)

def log_success(msg: str):
    print(f"{Color.GREEN}[✓]{Color.RESET} {Color.BOLD}{msg}{Color.RESET}", flush=True)

def log_warning(msg: str):
    print(f"{Color.YELLOW}[!]{Color.RESET} {msg}", flush=True)

def log_error(msg: str):
    print(f"{Color.RED}[✗]{Color.RESET} {msg}", flush=True)


# -----------------------------------------------------------------------------
# DETECÇÃO AUTOMÁTICA DE INSTALAÇÕES DO DISCORD
# -----------------------------------------------------------------------------

def find_discord_installations() -> List[Dict[str, str]]:
    """Localiza todos os executáveis do Discord disponíveis no sistema."""
    installs = []
    
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        app_data = os.environ.get("APPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        
        flavors = [
            ("Discord (Stable)", "Discord", "Discord.exe"),
            ("Discord Canary", "DiscordCanary", "DiscordCanary.exe"),
            ("Discord PTB", "DiscordPTB", "DiscordPTB.exe"),
            ("Discord Development", "DiscordDevelopment", "DiscordDevelopment.exe"),
        ]
        
        for name, folder, exe_name in flavors:
            app_pattern = os.path.join(local_app_data, folder, "app-*", exe_name)
            matches = glob.glob(app_pattern)
            if matches:
                matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                installs.append({
                    "name": name,
                    "type": "direct",
                    "path": matches[0],
                    "folder": folder
                })
            else:
                updater = os.path.join(local_app_data, folder, "Update.exe")
                if os.path.exists(updater):
                    installs.append({
                        "name": name,
                        "type": "updater",
                        "path": updater,
                        "folder": folder
                    })
        
        # Vesktop / Equibop
        vesktop_paths = [
            os.path.join(local_app_data, "Programs", "Vesktop", "Vesktop.exe"),
            os.path.join(prog_files, "Vesktop", "Vesktop.exe"),
            os.path.join(prog_files_x86, "Vesktop", "Vesktop.exe"),
            os.path.join(app_data, "Vesktop", "Vesktop.exe"),
        ]
        for vp in vesktop_paths:
            if os.path.exists(vp):
                installs.append({
                    "name": "Vesktop (Vencord Client)",
                    "type": "direct",
                    "path": vp,
                    "folder": "Vesktop"
                })
                break

    elif sys.platform == "darwin":
        mac_apps = [
            ("Discord (Stable)", "/Applications/Discord.app/Contents/MacOS/Discord"),
            ("Discord Canary", "/Applications/Discord Canary.app/Contents/MacOS/Discord Canary"),
            ("Discord PTB", "/Applications/Discord PTB.app/Contents/MacOS/Discord PTB"),
            ("Vesktop", "/Applications/Vesktop.app/Contents/MacOS/Vesktop")
        ]
        for name, path in mac_apps:
            if os.path.exists(path):
                installs.append({"name": name, "type": "direct", "path": path, "folder": "Discord"})
                
    else:  # Linux
        linux_bins = [
            ("Discord (Stable)", "discord"),
            ("Discord Canary", "discord-canary"),
            ("Discord PTB", "discord-ptb"),
            ("Vesktop", "vesktop")
        ]
        for name, cmd in linux_bins:
            path = subprocess.getoutput(f"which {cmd} 2>/dev/null").strip()
            if path and os.path.exists(path):
                installs.append({"name": name, "type": "direct", "path": path, "folder": "Discord"})
                
    return installs


def kill_discord_processes():
    """Finaliza processos em execução do Discord para permitir reinício limpo."""
    if sys.platform == "win32":
        targets = ["Discord.exe", "DiscordCanary.exe", "DiscordPTB.exe", "DiscordDevelopment.exe", "Vesktop.exe"]
        for target in targets:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception:
                pass
    else:
        try:
            subprocess.run(["pkill", "-9", "-f", "discord|vesktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# TESTE ULTRA-RÁPIDO DE PROXIES (PARALELO)
# -----------------------------------------------------------------------------

def test_socks5_handshake(host: str, port: int, timeout: float = 0.8) -> Optional[int]:
    """Testa handshake SOCKS5 instantâneo contra discord.com:443."""
    t0 = time.time()
    try:
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"\x05\x01\x00")
        if s.recv(2) == b"\x05\x00":
            target = b"discord.com"
            req = b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", 443)
            s.sendall(req)
            res = s.recv(10)
            s.close()
            if len(res) >= 2 and res[0] == 5 and res[1] == 0:
                return round((time.time() - t0) * 1000)
    except Exception:
        pass
    return None


def test_http_handshake(host: str, port: int, timeout: float = 0.8) -> Optional[int]:
    """Testa túnel CONNECT HTTP instantâneo contra discord.com:443."""
    t0 = time.time()
    try:
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        req = "CONNECT discord.com:443 HTTP/1.1\r\nHost: discord.com:443\r\nUser-Agent: Mozilla/5.0\r\n\r\n"
        s.sendall(req.encode("latin1"))
        res = s.recv(512).decode("latin1", errors="ignore")
        s.close()
        if "200" in res:
            return round((time.time() - t0) * 1000)
    except Exception:
        pass
    return None


def check_tor_local() -> Optional[str]:
    """Verifica se o Tor está rodando localmente (resposta em < 20ms)."""
    for port in [9050, 9150]:
        ms = test_socks5_handshake("127.0.0.1", port, timeout=0.15)
        if ms is not None:
            return f"socks5://127.0.0.1:{port}"
    return None


def fast_proxy_race() -> Optional[Dict]:
    """Testa simultaneamente em paralelo o pool de nós rápidos (retorna em < 0.4s)."""
    def worker(entry):
        proto, host, port, country = entry
        if proto == "socks5":
            ms = test_socks5_handshake(host, port, timeout=0.7)
        else:
            ms = test_http_handshake(host, port, timeout=0.7)
            
        if ms is not None:
            return {
                "proto": proto,
                "host": host,
                "port": port,
                "country": country,
                "latency": ms,
                "url": f"{proto}://{host}:{port}"
            }
        return None

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(worker, item) for item in FAST_RELAYS]
        for f in as_completed(futures):
            res = f.result()
            if res:
                return res
    return None


# -----------------------------------------------------------------------------
# CACHE DE PROXIES
# -----------------------------------------------------------------------------

def save_to_cache(proxy_info: Dict):
    try:
        proxy_info["timestamp"] = time.time()
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(proxy_info, f)
    except Exception:
        pass


def load_from_cache() -> Optional[Dict]:
    """Carrega do cache se for recente (< 2 horas) com validação rápida de 0.3s."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            proto = data.get("proto", "socks5")
            host = data.get("host")
            port = data.get("port")
            ts = data.get("timestamp", 0)
            # Se for recente (< 2 horas), revalida em 0.3s
            if host and port and (time.time() - ts < 7200):
                if proto == "socks5":
                    lat = test_socks5_handshake(host, port, timeout=0.35)
                else:
                    lat = test_http_handshake(host, port, timeout=0.35)
                if lat is not None:
                    data["latency"] = lat
                    return data
    except Exception:
        pass
    return None


def clear_cache():
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# LAUNCH DO DISCORD
# -----------------------------------------------------------------------------

def launch_discord(install: Dict[str, str], proxy_url: Optional[str] = None):
    """Executa o Discord com ou sem proxy."""
    cmd = []
    if proxy_url:
        proxy_arg = f'--proxy-server={proxy_url}'
        if sys.platform == "win32":
            if install["type"] == "updater":
                cmd = [install["path"], "--processStart", f"{install['folder']}.exe", "--process-args", proxy_arg]
            else:
                cmd = [install["path"], proxy_arg]
        else:
            cmd = [install["path"], proxy_arg]
    else:
        if sys.platform == "win32":
            if install["type"] == "updater":
                cmd = [install["path"], "--processStart", f"{install['folder']}.exe"]
            else:
                cmd = [install["path"]]
        else:
            cmd = [install["path"]]
        
    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, close_fds=True)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        
        if proxy_url:
            log_success(f"{install['name']} iniciado com sucesso através da proxy!")
        else:
            log_success(f"{install['name']} iniciado normalmente sem proxy!")
    except Exception as e:
        log_error(f"Falha ao iniciar o Discord: {e}")


def disable_bypass():
    """Desativa o bypass, limpa o cache e reinicia o Discord de forma padrão."""
    log_warning("Desativando LiveFreeBrasil e restaurando Discord normal...")
    kill_discord_processes()
    time.sleep(0.2)
    clear_cache()
    
    installs = find_discord_installations()
    if installs:
        launch_discord(installs[0], proxy_url=None)
        print(f"\n{Color.GREEN}{Color.BOLD}[✓] Bypass desativado!{Color.RESET}")
        print(f"{Color.WHITE}O Discord está rodando normalmente na sua conexão padrão.{Color.RESET}\n")
    else:
        log_error("Nenhuma instalação do Discord encontrada.")


# -----------------------------------------------------------------------------
# CLI E MODO INTERATIVO
# -----------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="LiveFreeBrasil CLI — Inicia o Discord Desktop com proxy fora do Brasil para liberar Live e Câmera.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("-p", "--proxy", type=str, help="Proxy customizada (Ex: socks5://127.0.0.1:9050)")
    parser.add_argument("-t", "--tor", action="store_true", help="Força Tor local (127.0.0.1:9050)")
    parser.add_argument("-a", "--auto", action="store_true", help="Modo 100% automático e instantâneo")
    parser.add_argument("--disable", "--restore", "--normal", dest="disable", action="store_true", help="Desativa o bypass")
    parser.add_argument("-k", "--kill", action="store_true", help="Encerra instâncias anteriores do Discord")
    parser.add_argument("--no-kill", action="store_true", help="Não encerra instâncias abertas")
    parser.add_argument("-d", "--discord", type=str, help="Caminho do executável do Discord")
    parser.add_argument("--list-proxies", action="store_true", help="Apenas testa proxies e encerra")
    parser.add_argument("-v", "--version", action="version", version=f"LiveFreeBrasil CLI v{VERSION}")
    
    return parser.parse_args()


def interactive_menu(installs: List[Dict[str, str]]) -> str:
    target_name = installs[0]["name"] if installs else "Discord"
    print(f"{Color.BOLD}Selecione a ação desejada:{Color.RESET}")
    print(f"  [1] {Color.GREEN}{Color.BOLD}Ativar Bypass (Instantâneo){Color.RESET} -> Conexão ultra-rápida e abre o {target_name}")
    print(f"  [2] {Color.RED}{Color.BOLD}Desativar Bypass (Modo Normal){Color.RESET} -> Limpa configurações e abre sem proxy")
    print(f"  [3] {Color.CYAN}Usar Tor Local{Color.RESET} (127.0.0.1:9050 ou 9150)")
    print(f"  [4] {Color.YELLOW}Informar Proxy Manualmente{Color.RESET}")
    print(f"  [5] {Color.DIM}Sair{Color.RESET}")
    
    while True:
        try:
            choice = input(f"\n{Color.CYAN}Opção [1-5] (padrão: 1): {Color.RESET}").strip()
            if not choice or choice == "1":
                return "auto"
            elif choice == "2":
                return "disable"
            elif choice == "3":
                return "tor"
            elif choice == "4":
                return "manual"
            elif choice == "5":
                sys.exit(0)
        except ValueError:
            pass


def resolve_proxy_instant(manual_proxy: Optional[str], force_tor: bool) -> Optional[Dict]:
    """Resolve a proxy com resposta em menos de 0.5 segundos."""
    # 1. Manual
    if manual_proxy:
        url = manual_proxy if "://" in manual_proxy else f"http://{manual_proxy}"
        return {"url": url, "country": "Manual", "latency": 0}

    # 2. Tor local forçado
    if force_tor:
        tor_url = check_tor_local()
        if tor_url:
            return {"url": tor_url, "country": "Rede Tor (Anônimo)", "latency": 10}
        log_error("Tor local não encontrado nas portas 9050 ou 9150.")
        return None

    # 3. Tor local automático (se já estiver aberto, usa em 10ms)
    tor_url = check_tor_local()
    if tor_url:
        log_success(f"Tor detectado: {Color.BOLD}{tor_url}{Color.RESET}")
        return {"url": tor_url, "country": "Rede Tor", "latency": 10}

    # 4. Cache recente validado em 0.2s
    cached = load_from_cache()
    if cached:
        log_success(f"Rota em cache: {Color.BOLD}{cached['url']}{Color.RESET} ({cached.get('country', 'Internacional')}, {cached['latency']}ms)")
        return cached

    # 5. Corrida paralela ultra-rápida entre relays internacionais
    log_info("Conectando ao relay internacional mais rápido...")
    fast = fast_proxy_race()
    if fast:
        log_success(f"Rota conectada: {Color.BOLD}{fast['url']}{Color.RESET} [{fast.get('country', 'Internacional')}] ({fast['latency']}ms)")
        save_to_cache(fast)
        return fast

    return None


def main():
    if sys.platform == "win32":
        os.system("")

    print_banner()
    args = parse_args()

    if args.disable:
        disable_bypass()
        return

    if args.list_proxies:
        p = fast_proxy_race()
        if p:
            log_success(f"Melhor proxy ativa: {p['url']} ({p['country']}) - Ping: {p['latency']}ms")
        return

    # 1. Localiza Discord
    installs = find_discord_installations()
    selected_install = None

    if args.discord:
        if os.path.exists(args.discord):
            selected_install = {"name": "Discord Custom", "type": "direct", "path": args.discord, "folder": "Discord"}
    elif installs:
        selected_install = installs[0]
        
    if not selected_install:
        log_error("Nenhuma instalação do Discord encontrada.")
        sys.exit(1)

    # 2. Modo de execução
    force_tor = args.tor
    manual_proxy_url = args.proxy

    if not args.auto and not args.proxy and not args.tor and not args.kill:
        action = interactive_menu(installs)
        if action == "disable":
            disable_bypass()
            return
        elif action == "tor":
            force_tor = True
        elif action == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Endereço da proxy: {Color.RESET}").strip()

    # 3. Encerra instâncias antigas rapidamente
    if not args.no_kill:
        kill_discord_processes()
        time.sleep(0.2)

    # 4. Resolve proxy instantaneamente (< 0.4s)
    proxy_data = resolve_proxy_instant(manual_proxy_url, force_tor=force_tor)
    
    if not proxy_data:
        log_error("Não foi possível obter uma proxy funcional fora do Brasil.")
        sys.exit(1)

    # 5. Inicia o Discord
    print("-" * 66, flush=True)
    log_info(f"Discord: {Color.BOLD}{selected_install['name']}{Color.RESET}")
    log_info(f"Rota Internacional: {Color.GREEN}{Color.BOLD}{proxy_data['url']}{Color.RESET} ({proxy_data.get('country', 'Internacional')})")
    print("-" * 66, flush=True)
    
    launch_discord(selected_install, proxy_data["url"])
    
    print(f"\n{Color.GREEN}{Color.BOLD}Tudo pronto!{Color.RESET} Live e Câmera liberadas.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}[!] Cancelado.{Color.RESET}")
        sys.exit(0)
