#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal
Motor de Conexão Internacional Resiliente, Diagnóstico Completo & Sistema de Logs
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

VERSION = "2.4.0"

# Diretórios base
LOCAL_APP_DATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
APP_DIR = os.path.join(LOCAL_APP_DATA, "LiveFreeBrasil")
TOR_DIR = os.path.join(APP_DIR, "tor")
TOR_DATA_DIR = os.path.join(APP_DIR, "tor_data")
LOG_FILE = os.path.join(APP_DIR, "livefreebrasil.log")
TOR_DOWNLOAD_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/14.0.5/tor-expert-bundle-windows-x86_64-14.0.5.tar.gz"

os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(TOR_DATA_DIR, exist_ok=True)

# Configura encoding de saída para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Pool de rotas internacionais de backup caso o Tor falhe
BACKUP_PROXIES = [
    ("socks5", "200.50.249.224", 1080, "Argentina"),
    ("socks5", "170.245.50.65", 1080, "Chile"),
    ("socks5", "190.61.43.122", 1080, "Colômbia"),
    ("socks5", "144.172.101.188", 1080, "Estados Unidos"),
    ("socks5", "72.195.34.40", 4145, "Estados Unidos"),
    ("socks5", "68.71.249.152", 4145, "Canadá"),
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


def write_log(msg: str, level: str = "INFO"):
    """Escreve eventos com timestamp no arquivo de log do LiveFreeBrasil."""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{ts}] [{level}] {msg}\n"
        with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as f:
            f.write(log_line)
    except Exception:
        pass


def print_banner():
    banner = rf"""
{Color.GREEN}{Color.BOLD}==================================================================
  _     _           _____              ____                 _ _ 
 | |   (_)_   _____|  ___| __ ___  ___| __ ) _ __ __ _ ___ (_) |
 | |   | \ \ / / _ \ |_ | '__/ _ \/ _ \  _ \| '__/ _` / __|| | |
 | |___| |\ V /  __/  _|| | |  __/  __/ |_) | | | (_| \__ \| | |
 |_____|_| \_/ \___|_|  |_|  \___|\___|____/|_|  \__,_|___/|_|_|
                                                                
{Color.WHITE}{Color.BOLD}  LiveFreeBrasil — Desbloqueio de Tela & Câmera no Discord v{VERSION}
{Color.CYAN}  🛡️ Motor Internacional 100% Autônomo com Diagnóstico e Logs
{Color.GREEN}=================================================================={Color.RESET}
"""
    print(banner, flush=True)


def log_info(msg: str):
    write_log(msg, "INFO")
    print(f"{Color.BLUE}[*]{Color.RESET} {msg}", flush=True)


def log_success(msg: str):
    write_log(msg, "SUCCESS")
    print(f"{Color.GREEN}[✓]{Color.RESET} {Color.BOLD}{msg}{Color.RESET}", flush=True)


def log_warning(msg: str):
    write_log(msg, "WARN")
    print(f"{Color.YELLOW}[!]{Color.RESET} {msg}", flush=True)


def log_error(msg: str):
    write_log(msg, "ERROR")
    print(f"{Color.RED}[✗]{Color.RESET} {msg}", flush=True)


# -----------------------------------------------------------------------------
# DETECÇÃO E ENCERRAMENTO FORÇADO DE PROCESSOS DO DISCORD
# -----------------------------------------------------------------------------

def kill_discord_processes():
    """Garante o encerramento total da árvore de processos do Discord para evitar Single Instance Lock."""
    write_log("Encerrando processos antigos do Discord...", "INFO")
    if sys.platform == "win32":
        targets = ["Discord.exe", "DiscordCanary.exe", "DiscordPTB.exe", "DiscordDevelopment.exe", "Vesktop.exe", "Update.exe"]
        for target in targets:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/IM", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
    else:
        try:
            subprocess.run(["pkill", "-9", "-f", "discord|vesktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


def clean_discord_gpu_cache():
    """Limpa caches corrompidos de GPU e Renderer que causam tela preta no Electron."""
    if sys.platform != "win32":
        return
    app_data = os.environ.get("APPDATA", "")
    if not app_data:
        return
    targets = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
    for t in targets:
        base_dir = os.path.join(app_data, t)
        if os.path.exists(base_dir):
            for sub in ["GPUCache", "Code Cache", "DawnCache", "Cache"]:
                p = os.path.join(base_dir, sub)
                if os.path.exists(p):
                    try:
                        shutil.rmtree(p, ignore_errors=True)
                    except Exception:
                        pass
    write_log("Caches corrompidos de GPU e Renderer limpos com sucesso.", "INFO")


def find_discord_installations() -> List[Dict[str, str]]:
    """Localiza todos os executáveis do Discord disponíveis no sistema, priorizando o binário direto app-*."""
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
        
        # Vesktop
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
                
    write_log(f"Instalações do Discord encontradas: {[i['name'] + ' (' + i['path'] + ')' for i in installs]}", "INFO")
    return installs


# -----------------------------------------------------------------------------
# VALIDAÇÃO PROFUNDA DE CONEXÃO (HTTPS + GATEWAY WEBSOCKET)
# -----------------------------------------------------------------------------

def test_socks_connectivity(host: str = "127.0.0.1", port: int = 9050, timeout: float = 1.2) -> Optional[int]:
    """Testa handshake SOCKS5 e handshake TLS direto com discord.com:443."""
    t0 = time.time()
    try:
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"\x05\x01\x00")
        if s.recv(2) != b"\x05\x00":
            s.close()
            return None
            
        target = b"discord.com"
        req = b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", 443)
        s.sendall(req)
        res = s.recv(10)
        if len(res) < 2 or res[0] != 5 or res[1] != 0:
            s.close()
            return None
            
        ctx = ssl.create_default_context()
        ss = ctx.wrap_socket(s, server_hostname="discord.com")
        ss.sendall(b"HEAD / HTTP/1.1\r\nHost: discord.com\r\nConnection: close\r\n\r\n")
        reply = ss.recv(128)
        ss.close()
        if reply:
            return round((time.time() - t0) * 1000)
    except Exception:
        pass
    return None


def test_gateway_tls(host: str = "127.0.0.1", port: int = 9050, timeout: float = 1.5) -> Optional[int]:
    """Testa handshake TLS WebSocket direto com gateway.discord.gg:443."""
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
        reply = ss.recv(128)
        ss.close()
        if reply:
            return round((time.time() - t0) * 1000)
    except Exception:
        pass
    return None


# -----------------------------------------------------------------------------
# GERENCIAMENTO DO MOTOR TOR NATIVO 100% SILENCIOSO
# -----------------------------------------------------------------------------

def find_tor_binary_and_data() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Localiza o tor.exe e os arquivos geoip/geoip6 em todas as pastas possíveis."""
    user_home = os.path.expanduser("~")
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    
    candidates = [
        # Pasta autônoma do LiveFreeBrasil
        (
            os.path.join(TOR_DIR, "tor", "tor.exe"),
            os.path.join(TOR_DIR, "data", "geoip"),
            os.path.join(TOR_DIR, "data", "geoip6")
        ),
        (
            os.path.join(TOR_DIR, "tor.exe"),
            os.path.join(TOR_DIR, "geoip"),
            os.path.join(TOR_DIR, "geoip6")
        ),
        # Tor Browser Desktop
        (
            os.path.join(user_home, "Desktop", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(user_home, "Desktop", "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip"),
            os.path.join(user_home, "Desktop", "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip6")
        ),
        # OneDrive Desktop
        (
            os.path.join(user_home, "OneDrive", "Desktop", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(user_home, "OneDrive", "Desktop", "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip"),
            os.path.join(user_home, "OneDrive", "Desktop", "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip6")
        ),
        # Program Files
        (
            os.path.join(os.environ.get("ProgramFiles", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip6")
        ),
        (
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tor Browser", "Browser", "TorBrowser", "Data", "Tor", "geoip6")
        )
    ]
    
    for t_exe, g, g6 in candidates:
        if os.path.exists(t_exe):
            return t_exe, g if os.path.exists(g) else None, g6 if os.path.exists(g6) else None
            
    return None, None, None


def download_and_extract_tor() -> Optional[str]:
    """Baixa o pacote oficial do Tor Expert Bundle silenciosamente caso o usuário não tenha o Tor."""
    log_info("Baixando motor Tor oficial (~14MB)...")
    write_log("Iniciando download do Tor Expert Bundle oficial...", "INFO")
    tar_path = os.path.join(APP_DIR, "tor_bundle.tar.gz")
    
    try:
        def report(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
            percent = min(percent, 100)
            sys.stdout.write(f"\r{Color.CYAN}[*] Baixando Tor: {percent}% concluído...{Color.RESET}")
            sys.stdout.flush()

        urllib.request.urlretrieve(TOR_DOWNLOAD_URL, tar_path, reporthook=report)
        print("", flush=True)
        
        log_info("Extraindo arquivos do motor Tor...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=TOR_DIR)
            
        try:
            os.remove(tar_path)
        except Exception:
            pass
            
        t_exe, _, _ = find_tor_binary_and_data()
        if t_exe:
            log_success("Motor Tor instalado com sucesso!")
            write_log(f"Tor instalado com sucesso em: {t_exe}", "SUCCESS")
            return t_exe
    except Exception as e:
        log_error(f"Falha no download automático do Tor: {e}")
        write_log(f"Erro no download do Tor: {e}", "ERROR")
        
    return None


def start_silent_tor_daemon() -> Optional[str]:
    """Inicia o daemon do Tor 100% invisível em segundo plano e conecta com retry e timeout inteligente."""
    # 1. Checa se já está rodando
    if test_socks_connectivity("127.0.0.1", 9050, timeout=0.4):
        log_success(f"Motor Tor já ativo em segundo plano: {Color.BOLD}socks5://127.0.0.1:9050{Color.RESET}")
        return "socks5://127.0.0.1:9050"
    if test_socks_connectivity("127.0.0.1", 9150, timeout=0.4):
        log_success(f"Tor Browser ativo: {Color.BOLD}socks5://127.0.0.1:9150{Color.RESET}")
        return "socks5://127.0.0.1:9150"

    # 2. Localiza ou baixa os binários
    tor_exe, geoip, geoip6 = find_tor_binary_and_data()
    if not tor_exe:
        tor_exe = download_and_extract_tor()
        if tor_exe:
            tor_exe, geoip, geoip6 = find_tor_binary_and_data()

    if not tor_exe:
        log_error("Não foi possível localizar ou instalar o Tor.")
        return None

    # 3. Mata instâncias zumbis
    subprocess.run(["taskkill", "/F", "/IM", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    time.sleep(0.3)

    # 4. Inicia processo com DataDirectory isolado
    cmd = [tor_exe, "--DataDirectory", TOR_DATA_DIR, "--SocksPort", "9050"]
    if geoip and geoip6:
        cmd.extend(["--GeoIPFile", geoip, "--GeoIPv6File", geoip6])

    log_info("Iniciando motor Tor silencioso em segundo plano...")
    write_log(f"Comando Tor: {' '.join(cmd)}", "INFO")
    CREATE_NO_WINDOW = 0x08000000
    try:
        subprocess.Popen(
            cmd,
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        log_error(f"Falha ao iniciar processo Tor: {e}")
        write_log(f"Falha ao iniciar processo Tor: {e}", "ERROR")
        return None

    # 5. Monitora prontidão real de tráfego HTTPS
    write_log("Aguardando circuito de criptografia do Tor...", "INFO")
    for i in range(30):
        time.sleep(0.5)
        ms = test_socks_connectivity("127.0.0.1", 9050, timeout=0.4)
        if ms is not None:
            print("", flush=True)
            log_success(f"Túnel Tor conectado e validado com sucesso! (Ping: {ms}ms)")
            write_log(f"Tor 100% pronto em 127.0.0.1:9050 ({ms}ms)", "SUCCESS")
            return "socks5://127.0.0.1:9050"
            
        sys.stdout.write(f"\r{Color.CYAN}[*] Estabelecendo circuito seguro com a rede internacional... ({int((i+1)/30*100)}%){Color.RESET}")
        sys.stdout.flush()
    print("", flush=True)

    if test_socks_connectivity("127.0.0.1", 9050, timeout=1.0):
        return "socks5://127.0.0.1:9050"

    write_log("Tor não conectou dentro do tempo limite.", "WARN")
    return None


def get_fast_backup_proxy() -> Optional[Dict]:
    """Testa concorrentemente o pool de rotas internacionais de backup."""
    log_info("Buscando rota internacional alternativa de alta velocidade...")
    write_log("Buscando backup proxies...", "INFO")
    tested = []

    def worker(entry):
        proto, host, port, country = entry
        ms = test_gateway_tls(host, port, timeout=1.2)
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

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, item) for item in BACKUP_PROXIES]
        for f in as_completed(futures):
            res = f.result()
            if res:
                tested.append(res)
                if len(tested) >= 2:
                    break

    if tested:
        tested.sort(key=lambda x: x["latency"])
        best = tested[0]
        write_log(f"Melhor rota de backup selecionada: {best['url']} ({best['country']}, {best['latency']}ms)", "INFO")
        return best

    return None


def kill_tor_processes():
    """Encerra processos do Tor."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            subprocess.run(["taskkill", "/F", "/IM", "firefox.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# LAUNCH DO DISCORD COM REPASSE DIRETO DE ARGUMENTOS
# -----------------------------------------------------------------------------

def launch_discord(install: Dict[str, str], proxy_url: Optional[str] = None):
    """Dispara o Discord garantindo o encerramento prévio e o repasse puro de argumentos."""
    clean_discord_gpu_cache()
    
    cmd = []
    if proxy_url:
        proxy_arg = f'--proxy-server={proxy_url}'
        if sys.platform == "win32":
            if install["type"] == "updater":
                # Tenta localizar o app-* direto para evitar que o Update.exe engula argumentos
                folder_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), install["folder"])
                direct_exes = glob.glob(os.path.join(folder_path, "app-*", f"{install['folder']}.exe"))
                if direct_exes:
                    direct_exes.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    cmd = [direct_exes[0], proxy_arg]
                else:
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
        
    write_log(f"Comando de inicialização do Discord: {' '.join(cmd)}", "INFO")
    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, close_fds=True)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        
        if proxy_url:
            log_success(f"{install['name']} iniciado com sucesso no modo {Color.BOLD}LiveFreeBrasil{Color.RESET}!")
            write_log("Discord iniciado com proxy.", "SUCCESS")
        else:
            log_success(f"{install['name']} iniciado normalmente sem proxy!")
            write_log("Discord iniciado sem proxy.", "SUCCESS")
    except Exception as e:
        log_error(f"Falha ao iniciar o Discord: {e}")
        write_log(f"Falha ao iniciar o Discord: {e}", "ERROR")


def disable_bypass():
    """Desativa completamente o bypass e restaura o Discord padrão."""
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
# SISTEMA DE DIAGNÓSTICO E LOGS
# -----------------------------------------------------------------------------

def run_diagnostic():
    """Executa bateria de testes de rede e exibe o status de saúde da rota."""
    print(f"\n{Color.BOLD}{Color.CYAN}=== Diagnóstico de Conectividade do LiveFreeBrasil ==={Color.RESET}\n")
    
    # 1. Verifica Discord instalado
    installs = find_discord_installations()
    if installs:
        print(f"{Color.GREEN}[✓] Discord Detectado:{Color.RESET} {installs[0]['name']} ({installs[0]['path']})")
    else:
        print(f"{Color.RED}[✗] Discord Não Encontrado:{Color.RESET} Nenhuma instalação padrão localizada.")

    # 2. Testa Tor Local (9050 / 9150)
    tor_9050 = test_socks_connectivity("127.0.0.1", 9050, timeout=1.0)
    tor_9150 = test_socks_connectivity("127.0.0.1", 9150, timeout=1.0)
    
    if tor_9050 is not None:
        print(f"{Color.GREEN}[✓] Motor Tor Daemon (127.0.0.1:9050):{Color.RESET} ONLINE ({tor_9050}ms)")
    else:
        print(f"{Color.YELLOW}[!] Motor Tor Daemon (127.0.0.1:9050):{Color.RESET} Inativo")
        
    if tor_9150 is not None:
        print(f"{Color.GREEN}[✓] Tor Browser (127.0.0.1:9150):{Color.RESET} ONLINE ({tor_9150}ms)")
    else:
        print(f"{Color.DIM}[-] Tor Browser (127.0.0.1:9150): Fechado{Color.RESET}")

    # 3. Testa Gateway WebSocket do Discord
    gw_ms = test_gateway_tls("127.0.0.1", 9050 if tor_9050 else (9150 if tor_9150 else 0), timeout=1.5)
    if gw_ms is not None:
        print(f"{Color.GREEN}[✓] Discord Gateway TLS (gateway.discord.gg):{Color.RESET} CONECTADO ({gw_ms}ms)")
    else:
        print(f"{Color.YELLOW}[!] Discord Gateway TLS:{Color.RESET} Aguardando inicialização do motor")

    # 4. Arquivo de log
    print(f"\n{Color.CYAN}[*] Arquivo de Log:{Color.RESET} {LOG_FILE}")
    if os.path.exists(LOG_FILE):
        print(f"{Color.DIM}    ↳ Últimos eventos registrados:{Color.RESET}")
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                for l in lines[-6:]:
                    print("      " + l.strip())
        except Exception:
            pass
            
    print(f"\n{Color.GREEN}{Color.BOLD}Diagnóstico concluído!{Color.RESET}\n")


# -----------------------------------------------------------------------------
# CLI E MODO INTERATIVO
# -----------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="LiveFreeBrasil CLI — Inicia o Discord Desktop com proxy fora do Brasil para liberar Live e Câmera.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("-t", "--tor", action="store_true", help="Usa o Tor silencioso em segundo plano")
    parser.add_argument("-p", "--proxy", type=str, help="Proxy customizada (Ex: socks5://127.0.0.1:9050)")
    parser.add_argument("-a", "--auto", action="store_true", help="Modo 100% automático e verificado")
    parser.add_argument("--diag", "--diagnostic", action="store_true", help="Executa diagnóstico de rede e exibe logs")
    parser.add_argument("--clean", "--clear-cache", action="store_true", help="Limpa cache gráfico da GPU do Discord")
    parser.add_argument("--disable", "--restore", "--normal", dest="disable", action="store_true", help="Desativa o bypass")
    parser.add_argument("-k", "--kill", action="store_true", help="Encerra instâncias anteriores do Discord")
    parser.add_argument("--no-kill", action="store_true", help="Não encerra instâncias abertas")
    parser.add_argument("-d", "--discord", type=str, help="Caminho do executável do Discord")
    parser.add_argument("-v", "--version", action="version", version=f"LiveFreeBrasil CLI v{VERSION}")
    
    return parser.parse_args()


def interactive_menu(installs: List[Dict[str, str]]) -> str:
    print(f"{Color.BOLD}Selecione a ação desejada:{Color.RESET}")
    print(f"  [1] {Color.GREEN}{Color.BOLD}Ativar Bypass (Motor Invisível - 100% Automático){Color.RESET}")
    print(f"      {Color.DIM}↳ Conecta sozinho em segundo plano. Live, Câmera e Streams 100% liberadas.{Color.RESET}")
    print(f"  [2] {Color.RED}Desativar Bypass (Modo Normal){Color.RESET} -> Abre direto sem proxy")
    print(f"  [3] {Color.MAGENTA}Limpar Cache Gráfico (Reparar Tela Preta){Color.RESET}")
    print(f"  [4] {Color.CYAN}Ver Diagnóstico & Logs de Conexão{Color.RESET}")
    print(f"  [5] {Color.WHITE}Informar Proxy Manualmente{Color.RESET}")
    print(f"  [6] {Color.DIM}Sair{Color.RESET}")
    
    while True:
        try:
            choice = input(f"\n{Color.CYAN}Opção [1-6] (padrão: 1): {Color.RESET}").strip()
            if not choice or choice == "1":
                return "tor"
            elif choice == "2":
                return "disable"
            elif choice == "3":
                return "clean"
            elif choice == "4":
                return "diag"
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

    if args.diag:
        run_diagnostic()
        return

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

    if not args.auto and not args.proxy and not args.tor and not args.kill:
        action = interactive_menu(installs)
        if action == "disable":
            disable_bypass()
            return
        elif action == "clean":
            kill_discord_processes()
            clean_discord_gpu_cache()
            log_success("Cache limpo!")
            return
        elif action == "diag":
            run_diagnostic()
            return
        elif action == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Endereço da proxy: {Color.RESET}").strip()
        else:
            mode = action

    # 3. Encerra instâncias antigas de forma segura
    if not args.no_kill:
        kill_discord_processes()
        time.sleep(0.3)

    # 4. Resolve rota internacional segura (com fallback automático resiliente)
    proxy_url = None
    country_label = "Motor Internacional"
    
    if manual_proxy_url:
        proxy_url = manual_proxy_url if "://" in manual_proxy_url else f"socks5://{manual_proxy_url}"
        country_label = "Manual"
    else:
        # Tenta motor Tor nativo
        proxy_url = start_silent_tor_daemon()
        if proxy_url:
            country_label = "Túnel Seguro (Tor)"
        else:
            # Fallback transparente para rota internacional pública
            log_warning("Túnel local indisponível. Alternando para rota internacional de alta velocidade...")
            backup = get_fast_backup_proxy()
            if backup:
                proxy_url = backup["url"]
                country_label = f"Backup ({backup['country']})"

    if not proxy_url:
        log_error("Não foi possível estabelecer uma rota de saída internacional.")
        log_info("Dica: Execute 'LiveFreeBrasil.exe --diag' para verificar sua conectividade.")
        sys.exit(1)

    # 5. Inicia o Discord com rota liberada
    print("-" * 66, flush=True)
    log_info(f"Discord: {Color.BOLD}{selected_install['name']}{Color.RESET}")
    log_info(f"Rota Internacional: {Color.GREEN}{Color.BOLD}{proxy_url}{Color.RESET} ({country_label})")
    print("-" * 66, flush=True)
    
    launch_discord(selected_install, proxy_url)
    
    print(f"\n{Color.GREEN}{Color.BOLD}Tudo pronto!{Color.RESET} Discord iniciado com Go Live, Câmera e Streams 100% liberados.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}[!] Cancelado.{Color.RESET}")
        sys.exit(0)
