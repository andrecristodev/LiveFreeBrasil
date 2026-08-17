#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal
Motor Tor Local Integrado com Autoinstalação e Auto-Start 100% Transparente
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
import shutil
import tarfile
import subprocess
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple

VERSION = "2.0.0"
CREATOR = "@tadalas"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".livefreebrasil_cache.json")

TOR_DOWNLOAD_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/14.0.5/tor-expert-bundle-windows-x86_64-14.0.5.tar.gz"
TOR_BASE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "LiveFreeBrasil", "tor")

# Configura encoding de saída para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Pool de nós prioritários caso o usuário escolha modo proxies públicas
RELAYS_CANDIDATES = [
    ("socks5", "127.0.0.1", 9050, "Tor Local", False),
    ("socks5", "127.0.0.1", 9150, "Tor Local", False),
    ("socks5", "200.50.249.224", 1080, "Argentina", True),
    ("socks5", "170.245.50.65", 1080, "Chile", True),
    ("socks5", "190.61.43.122", 1080, "Colômbia", True),
    ("socks5", "144.172.101.188", 1080, "Estados Unidos", False),
    ("socks5", "72.195.34.40", 4145, "Estados Unidos", False),
    ("socks5", "68.71.249.152", 4145, "Canadá", False),
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
{Color.CYAN}  🧅 Motor Tor Standalone com Autoinstalação e Auto-Start
{Color.YELLOW}  Criado por: {Color.WHITE}{CREATOR} {Color.YELLOW}no Discord
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
# GERENCIAMENTO E AUTOINSTALAÇÃO DO MOTOR TOR INTEGRADO
# -----------------------------------------------------------------------------

def locate_tor_binary() -> Optional[str]:
    """Busca binários existentes do Tor no sistema."""
    possible_paths = [
        os.path.join(TOR_BASE_DIR, "tor", "tor.exe"),
        os.path.join(TOR_BASE_DIR, "tor.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
        os.path.join(os.path.expanduser("~"), "Desktop", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def is_tor_port_alive(port: int = 9050) -> bool:
    """Testa se uma porta SOCKS5 do Tor está ativa e respondendo."""
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=0.3)
        s.sendall(b"\x05\x01\x00")
        res = s.recv(2)
        s.close()
        return res == b"\x05\x00"
    except Exception:
        return False


def install_tor_standalone() -> Optional[str]:
    """Baixa e instala o Tor Expert Bundle oficial silenciosamente."""
    os.makedirs(TOR_BASE_DIR, exist_ok=True)
    tar_path = os.path.join(TOR_BASE_DIR, "tor_bundle.tar.gz")
    
    log_info("Instalando motor Tor oficial de alta estabilidade...")
    try:
        def report(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
            percent = min(percent, 100)
            sys.stdout.write(f"\r{Color.CYAN}[*] Baixando Tor: {percent}% concluído...{Color.RESET}")
            sys.stdout.flush()

        urllib.request.urlretrieve(TOR_DOWNLOAD_URL, tar_path, reporthook=report)
        print("", flush=True)
        
        log_info("Extraindo arquivos do Tor...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=TOR_BASE_DIR)
            
        try:
            os.remove(tar_path)
        except Exception:
            pass
            
        tor_exe = locate_tor_binary()
        if tor_exe:
            log_success("Motor Tor instalado com sucesso!")
            return tor_exe
    except Exception as e:
        log_error(f"Falha no download automático do Tor: {e}")
        
    return None


def ensure_tor_service_running() -> Optional[str]:
    """Garante que o Tor está ativo em 127.0.0.1:9050 ou 9150."""
    # 1. Se já tem Tor rodando
    if is_tor_port_alive(9050):
        return "socks5://127.0.0.1:9050"
    if is_tor_port_alive(9150):
        return "socks5://127.0.0.1:9150"

    # 2. Localiza ou instala o tor.exe
    tor_exe = locate_tor_binary()
    if not tor_exe:
        tor_exe = install_tor_standalone()

    if not tor_exe:
        log_error("Não foi possível inicializar o binário do Tor.")
        return None

    # 3. Inicia o Tor em segundo plano
    log_info("Iniciando serviço do Tor em segundo plano...")
    data_dir = os.path.join(TOR_BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    cmd = [tor_exe, "--SocksPort", "9050", "--DataDirectory", data_dir]
    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            
        # Aguarda a porta 9050 abrir (máximo 10s)
        for _ in range(20):
            time.sleep(0.5)
            if is_tor_port_alive(9050):
                log_success(f"Tor ativado e pronto: {Color.BOLD}socks5://127.0.0.1:9050{Color.RESET}")
                return "socks5://127.0.0.1:9050"
    except Exception as e:
        log_error(f"Erro ao iniciar processo do Tor: {e}")

    return None


def kill_tor_processes():
    """Encerra instâncias locais do Tor."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# LIMPEZA DE CACHE DA GPU
# -----------------------------------------------------------------------------

def clean_discord_gpu_cache():
    if sys.platform != "win32":
        return
    app_data = os.environ.get("APPDATA", "")
    if not app_data:
        return
    targets = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
    for t in targets:
        base_dir = os.path.join(app_data, t)
        if os.path.exists(base_dir):
            for sub in ["GPUCache", "Code Cache", "DawnCache"]:
                p = os.path.join(base_dir, sub)
                if os.path.exists(p):
                    try:
                        shutil.rmtree(p, ignore_errors=True)
                    except Exception:
                        pass


# -----------------------------------------------------------------------------
# DETECÇÃO AUTOMÁTICA DE INSTALAÇÕES DO DISCORD
# -----------------------------------------------------------------------------

def find_discord_installations() -> List[Dict[str, str]]:
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
                
    else:
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
    if sys.platform == "win32":
        targets = ["Discord.exe", "DiscordCanary.exe", "DiscordPTB.exe", "DiscordDevelopment.exe", "Vesktop.exe"]
        for target in targets:
            try:
                subprocess.run(["taskkill", "/F", "/IM", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
    else:
        try:
            subprocess.run(["pkill", "-9", "-f", "discord|vesktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# VALIDAÇÃO DE PROXIES PÚBLICAS
# -----------------------------------------------------------------------------

def validate_socks5_deep(host: str, port: int, timeout: float = 1.2) -> Optional[int]:
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


def find_verified_public_proxy(prefer_latam: bool = False) -> Optional[Dict]:
    candidates = list(RELAYS_CANDIDATES)
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

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, item) for item in candidates]
        for f in as_completed(futures):
            res = f.result()
            if res:
                tested.append(res)
                if len(tested) >= 2:
                    break

    if tested:
        tested.sort(key=lambda x: x["latency"])
        return tested[0]
    return None


# -----------------------------------------------------------------------------
# LAUNCH DO DISCORD
# -----------------------------------------------------------------------------

def launch_discord(install: Dict[str, str], proxy_url: Optional[str] = None):
    clean_discord_gpu_cache()
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
            log_success(f"{install['name']} iniciado com sucesso no modo {Color.BOLD}LiveFreeBrasil{Color.RESET}!")
        else:
            log_success(f"{install['name']} iniciado normalmente sem proxy!")
    except Exception as e:
        log_error(f"Falha ao iniciar o Discord: {e}")


def disable_bypass():
    log_warning("Desativando LiveFreeBrasil e restaurando Discord normal...")
    kill_discord_processes()
    kill_tor_processes()
    time.sleep(0.3)
    clean_discord_gpu_cache()
    
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
    
    parser.add_argument("-t", "--tor", action="store_true", help="Usa o Tor local integrado com auto-start")
    parser.add_argument("-p", "--proxy", type=str, help="Proxy customizada (Ex: socks5://127.0.0.1:9050)")
    parser.add_argument("-l", "--latam", action="store_true", help="Prioriza nós da América Latina")
    parser.add_argument("-a", "--auto", action="store_true", help="Modo 100% automático (usa Tor Integrado)")
    parser.add_argument("--clean", "--clear-cache", action="store_true", help="Limpa cache gráfico da GPU do Discord")
    parser.add_argument("--disable", "--restore", "--normal", dest="disable", action="store_true", help="Desativa o bypass")
    parser.add_argument("-k", "--kill", action="store_true", help="Encerra instâncias anteriores do Discord")
    parser.add_argument("--no-kill", action="store_true", help="Não encerra instâncias abertas")
    parser.add_argument("-d", "--discord", type=str, help="Caminho do executável do Discord")
    parser.add_argument("-v", "--version", action="version", version=f"LiveFreeBrasil CLI v{VERSION}")
    
    return parser.parse_args()


def interactive_menu(installs: List[Dict[str, str]]) -> str:
    target_name = installs[0]["name"] if installs else "Discord"
    print(f"{Color.BOLD}Selecione a ação desejada:{Color.RESET}")
    print(f"  [1] {Color.GREEN}{Color.BOLD}Ativar Bypass (Motor Tor Integrado - Recomendado){Color.RESET}")
    print(f"      {Color.DIM}↳ Autoinstala e inicia o Tor em segundo plano. 100% estável para Streams & Câmera.{Color.RESET}")
    print(f"  [2] {Color.YELLOW}Ativar Bypass com Proxies Públicas (América Latina / EUA){Color.RESET}")
    print(f"  [3] {Color.RED}Desativar Bypass (Modo Normal){Color.RESET} -> Abre direto sem proxy")
    print(f"  [4] {Color.MAGENTA}Limpar Cache Gráfico (Reparar Tela Preta){Color.RESET}")
    print(f"  [5] {Color.WHITE}Informar Proxy Manualmente{Color.RESET}")
    print(f"  [6] {Color.DIM}Sair{Color.RESET}")
    
    while True:
        try:
            choice = input(f"\n{Color.CYAN}Opção [1-6] (padrão: 1): {Color.RESET}").strip()
            if not choice or choice == "1":
                return "tor"
            elif choice == "2":
                return "public"
            elif choice == "3":
                return "disable"
            elif choice == "4":
                return "clean"
            elif choice == "5":
                return "manual"
            elif choice == "6":
                sys.exit(0)
        except ValueError:
            pass


def main():
    if sys.platform == "win32":
        os.system("")

    print_banner()
    args = parse_args()

    if args.clean:
        kill_discord_processes()
        clean_discord_gpu_cache()
        log_success("Limpeza de cache concluída!")
        return

    if args.disable:
        disable_bypass()
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
    mode = "tor" if (args.auto or args.tor) else None
    manual_proxy_url = args.proxy

    if not args.auto and not args.proxy and not args.tor and not args.latam and not args.kill:
        action = interactive_menu(installs)
        if action == "disable":
            disable_bypass()
            return
        elif action == "clean":
            kill_discord_processes()
            clean_discord_gpu_cache()
            log_success("Cache limpo!")
            return
        elif action == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Endereço da proxy: {Color.RESET}").strip()
        else:
            mode = action

    # 3. Encerra instâncias antigas
    if not args.no_kill:
        kill_discord_processes()
        time.sleep(0.3)

    # 4. Resolve proxy (com Motor Tor Integrado por padrão)
    proxy_url = None
    country_label = "Tor Integrado (Local)"
    
    if manual_proxy_url:
        proxy_url = manual_proxy_url if "://" in manual_proxy_url else f"socks5://{manual_proxy_url}"
        country_label = "Manual"
    elif mode == "public" or args.latam:
        log_info("Buscando melhor rota pública...")
        p = find_verified_public_proxy(prefer_latam=args.latam)
        if p:
            proxy_url = p["url"]
            country_label = p["country"]
        else:
            log_warning("Nenhuma proxy pública rápida respondeu. Alternando para o Tor Integrado...")
            proxy_url = ensure_tor_service_running()
    else:
        # Modo Tor Integrado (Padrão e Recomendado)
        proxy_url = ensure_tor_service_running()

    if not proxy_url:
        log_error("Não foi possível iniciar o serviço de conexão segura.")
        sys.exit(1)

    # 5. Inicia o Discord
    print("-" * 66, flush=True)
    log_info(f"Discord: {Color.BOLD}{selected_install['name']}{Color.RESET}")
    log_info(f"Rota Segura: {Color.GREEN}{Color.BOLD}{proxy_url}{Color.RESET} ({country_label})")
    print("-" * 66, flush=True)
    
    launch_discord(selected_install, proxy_url)
    
    print(f"\n{Color.GREEN}{Color.BOLD}Tudo pronto!{Color.RESET} Discord iniciado com Go Live, Câmera e Streams 100% liberados.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}[!] Cancelado.{Color.RESET}")
        sys.exit(0)
