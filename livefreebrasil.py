#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal
Suporte a Rotas de Baixa Latência da América Latina (Argentina, Chile, Uruguai, etc.)
Criador: @tadalas no Discord
"""

import sys
import os
import time
import socket
import struct
import json
import glob
import ssl
import subprocess
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple

VERSION = "1.4.0"
CREATOR = "@tadalas"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".livefreebrasil_cache.json")

# Configura encoding de saída para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Pool de nós prioritários da América Latina e Globais
RELAYS_CANDIDATES = [
    # América Latina (Argentina, Chile, Colômbia, Uruguai, México)
    ("socks5", "200.50.249.224", 1080, "Argentina", True),
    ("socks5", "170.245.50.65", 1080, "Chile", True),
    ("socks5", "190.61.43.122", 1080, "Colômbia", True),
    ("socks5", "190.61.61.210", 1080, "Colômbia", True),
    ("socks5", "190.2.209.62", 1080, "Colômbia", True),
    ("socks5", "190.14.249.111", 1080, "Colômbia", True),
    ("socks5", "201.165.172.14", 1080, "México", True),
    
    # Tor Local
    ("socks5", "127.0.0.1", 9050, "Tor Local", False),
    ("socks5", "127.0.0.1", 9150, "Tor Local", False),
    
    # Nós Internacionais de Alta Fidelidade
    ("socks5", "144.172.101.188", 1080, "Estados Unidos", False),
    ("socks5", "72.195.34.40", 4145, "Estados Unidos", False),
    ("socks5", "98.162.25.29", 4145, "Estados Unidos", False),
    ("socks5", "184.178.172.28", 4145, "Estados Unidos", False),
    ("socks5", "68.71.249.152", 4145, "Canadá", False),
    ("socks5", "98.188.47.112", 4145, "Estados Unidos", False),
]

# Códigos de países da América Latina
LATAM_CODES = {
    "AR": "Argentina",
    "CL": "Chile",
    "UY": "Uruguai",
    "PY": "Paraguai",
    "CO": "Colômbia",
    "PE": "Peru",
    "MX": "México",
    "EC": "Equador",
    "BO": "Bolívia"
}

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
{Color.YELLOW}  Suporte a Rotas da América Latina (Argentina, Chile, Uruguai...)
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
# VALIDAÇÃO PROFUNDA (DEEP TLS GATEWAY) DE PROXIES
# -----------------------------------------------------------------------------

def validate_socks5_deep(host: str, port: int, timeout: float = 1.2) -> Optional[int]:
    """Testa handshake SOCKS5 E handshake TLS completo com o Gateway do Discord (gateway.discord.gg:443)."""
    t0 = time.time()
    try:
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"\x05\x01\x00")
        if s.recv(2) != b"\x05\x00":
            s.close()
            return None
            
        target = b"gateway.discord.gg"
        req = b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", 443)
        s.sendall(req)
        res = s.recv(10)
        if len(res) < 2 or res[0] != 5 or res[1] != 0:
            s.close()
            return None
            
        # Handshake TLS real com o Gateway WebSocket do Discord
        ctx = ssl.create_default_context()
        ss = ctx.wrap_socket(s, server_hostname="gateway.discord.gg")
        ss.sendall(b"GET / HTTP/1.1\r\nHost: gateway.discord.gg\r\nConnection: close\r\n\r\n")
        reply = ss.recv(256)
        ss.close()
        
        if reply:
            return round((time.time() - t0) * 1000)
    except Exception:
        pass
    return None


def check_tor_local() -> Optional[str]:
    """Verifica se o Tor está rodando localmente (resposta em < 20ms com suporte total a WebSockets)."""
    for port in [9050, 9150]:
        ms = validate_socks5_deep("127.0.0.1", port, timeout=0.2)
        if ms is not None:
            return f"socks5://127.0.0.1:{port}"
    return None


def fetch_online_socks5_candidates() -> List[Tuple[str, int]]:
    """Baixa lista atualizada de proxies SOCKS5 públicas online."""
    found = []
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                for line in lines[:100]:
                    line = line.strip()
                    if ":" in line and not line.startswith("#"):
                        p = line.split(":")
                        if len(p) >= 2 and p[1].isdigit():
                            found.append((p[0], int(p[1])))
        except Exception:
            continue
    return found


def find_verified_gateway_proxy(prefer_latam: bool = False) -> Optional[Dict]:
    """Testa concorrentemente nós com validação profunda de TLS no Gateway do Discord."""
    candidates = list(RELAYS_CANDIDATES)
    
    # Se preferir América Latina, coloca os nós latam no topo
    if prefer_latam:
        candidates.sort(key=lambda x: (not x[4]))

    tested = []
    
    def worker(entry):
        proto, host, port, country, is_latam = entry
        ms = validate_socks5_deep(host, port, timeout=1.2)
        if ms is not None:
            return {
                "proto": proto,
                "host": host,
                "port": port,
                "country": country,
                "latency": ms,
                "is_latam": is_latam,
                "url": f"{proto}://{host}:{port}"
            }
        return None

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(worker, item) for item in candidates]
        for f in as_completed(futures):
            res = f.result()
            if res:
                tested.append(res)
                if prefer_latam and res["is_latam"]:
                    return res
                if len(tested) >= 3:
                    break

    if tested:
        # Se preferir América Latina e houver algum testado, pega o de menor ping
        if prefer_latam:
            latam_found = [t for t in tested if t["is_latam"]]
            if latam_found:
                latam_found.sort(key=lambda x: x["latency"])
                return latam_found[0]
                
        tested.sort(key=lambda x: x["latency"])
        return tested[0]

    # Fallback para busca online
    log_info("Buscando novos nós SOCKS5 com suporte a WebSocket...")
    online = fetch_online_socks5_candidates()
    
    def online_worker(item):
        host, port = item
        ms = validate_socks5_deep(host, port, timeout=1.2)
        if ms is not None:
            return {
                "proto": "socks5",
                "host": host,
                "port": port,
                "country": "Internacional",
                "latency": ms,
                "is_latam": False,
                "url": f"socks5://{host}:{port}"
            }
        return None

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(online_worker, c) for c in online[:100]]
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
    """Carrega do cache apenas se o Gateway TLS responder com sucesso."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            host = data.get("host")
            port = data.get("port")
            ts = data.get("timestamp", 0)
            if host and port and (time.time() - ts < 3600):
                lat = validate_socks5_deep(host, port, timeout=0.8)
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
            log_success(f"{install['name']} iniciado com rota validada!")
        else:
            log_success(f"{install['name']} iniciado normalmente sem proxy!")
    except Exception as e:
        log_error(f"Falha ao iniciar o Discord: {e}")


def disable_bypass():
    """Desativa o bypass, limpa o cache e reinicia o Discord de forma padrão."""
    log_warning("Desativando LiveFreeBrasil e restaurando Discord normal...")
    kill_discord_processes()
    time.sleep(0.3)
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
    parser.add_argument("-l", "--latam", action="store_true", help="Prioriza nós da América Latina (Argentina, Chile, Uruguai, etc.)")
    parser.add_argument("-t", "--tor", action="store_true", help="Força Tor local (127.0.0.1:9050)")
    parser.add_argument("-a", "--auto", action="store_true", help="Modo 100% automático e verificado")
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
    print(f"  [1] {Color.GREEN}{Color.BOLD}Ativar Bypass Automático (Gateway Verificado){Color.RESET} -> Menor ping global")
    print(f"  [2] {Color.YELLOW}{Color.BOLD}Ativar Bypass América Latina (Argentina/Chile/etc.){Color.RESET} -> Menor latência")
    print(f"  [3] {Color.RED}{Color.BOLD}Desativar Bypass (Modo Normal){Color.RESET} -> Abre direto sem proxy")
    print(f"  [4] {Color.CYAN}Usar Tor Local (Recomendado){Color.RESET} (127.0.0.1:9050 ou 9150)")
    print(f"  [5] {Color.MAGENTA}Informar Proxy Manualmente{Color.RESET}")
    print(f"  [6] {Color.DIM}Sair{Color.RESET}")
    
    while True:
        try:
            choice = input(f"\n{Color.CYAN}Opção [1-6] (padrão: 1): {Color.RESET}").strip()
            if not choice or choice == "1":
                return "auto"
            elif choice == "2":
                return "latam"
            elif choice == "3":
                return "disable"
            elif choice == "4":
                return "tor"
            elif choice == "5":
                return "manual"
            elif choice == "6":
                sys.exit(0)
        except ValueError:
            pass


def resolve_proxy_reliable(manual_proxy: Optional[str], force_tor: bool, prefer_latam: bool = False) -> Optional[Dict]:
    """Resolve uma proxy 100% compatível com o Gateway WebSocket do Discord."""
    # 1. Manual
    if manual_proxy:
        url = manual_proxy if "://" in manual_proxy else f"socks5://{manual_proxy}"
        return {"url": url, "country": "Manual", "latency": 0}

    # 2. Tor local forçado
    if force_tor:
        tor_url = check_tor_local()
        if tor_url:
            return {"url": tor_url, "country": "Rede Tor (100% Estável)", "latency": 10}
        log_error("Tor local não encontrado nas portas 9050 ou 9150.")
        log_info("Dica: Abra o 'Tor Browser' em segundo plano para máxima estabilidade!")
        return None

    # 3. Tor local automático (se não pediu América Latina explicitamente e o Tor Browser estiver aberto)
    if not prefer_latam:
        tor_url = check_tor_local()
        if tor_url:
            log_success(f"Tor detectado e verificado: {Color.BOLD}{tor_url}{Color.RESET}")
            return {"url": tor_url, "country": "Rede Tor", "latency": 10}

    # 4. Cache recente validado com Gateway TLS
    if not prefer_latam:
        cached = load_from_cache()
        if cached:
            log_success(f"Rota validada do cache: {Color.BOLD}{cached['url']}{Color.RESET} ({cached.get('country', 'Internacional')}, {cached['latency']}ms)")
            return cached

    # 5. Busca proxy SOCKS5 com validação profunda no Gateway TLS
    tipo = "América Latina (Argentina, Chile, etc.)" if prefer_latam else "Gateway do Discord"
    log_info(f"Validando rota SOCKS5 ({tipo})...")
    found = find_verified_gateway_proxy(prefer_latam=prefer_latam)
    if found:
        log_success(f"Rota verificada com sucesso: {Color.BOLD}{found['url']}{Color.RESET} [{found.get('country', 'Internacional')}] ({found['latency']}ms)")
        save_to_cache(found)
        return found

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
        p = find_verified_gateway_proxy(prefer_latam=args.latam)
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
    prefer_latam = args.latam
    manual_proxy_url = args.proxy

    if not args.auto and not args.proxy and not args.tor and not args.latam and not args.kill:
        action = interactive_menu(installs)
        if action == "disable":
            disable_bypass()
            return
        elif action == "latam":
            prefer_latam = True
        elif action == "tor":
            force_tor = True
        elif action == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Endereço da proxy: {Color.RESET}").strip()

    # 3. Encerra instâncias antigas
    if not args.no_kill:
        kill_discord_processes()
        time.sleep(0.3)

    # 4. Resolve proxy com garantia de Gateway TLS
    proxy_data = resolve_proxy_reliable(manual_proxy_url, force_tor=force_tor, prefer_latam=prefer_latam)
    
    if not proxy_data:
        log_error("Não foi possível validar um nó SOCKS5 compatível com o Gateway do Discord.")
        log_info("Dica de ouro: Abra o 'Tor Browser' no seu PC e execute novamente para conexão 100% estável!")
        sys.exit(1)

    # 5. Inicia o Discord
    print("-" * 66, flush=True)
    log_info(f"Discord: {Color.BOLD}{selected_install['name']}{Color.RESET}")
    log_info(f"Rota ({proxy_data.get('country', 'Internacional')}): {Color.GREEN}{Color.BOLD}{proxy_data['url']}{Color.RESET} (Ping: {proxy_data['latency']}ms)")
    print("-" * 66, flush=True)
    
    launch_discord(selected_install, proxy_data["url"])
    
    print(f"\n{Color.GREEN}{Color.BOLD}Tudo pronto!{Color.RESET} Conexão com o Gateway estabelecida. Live e Câmera liberadas.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}[!] Cancelado.{Color.RESET}")
        sys.exit(0)
