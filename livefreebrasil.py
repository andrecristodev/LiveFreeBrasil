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

VERSION = "1.1.0"
CREATOR = "@tadalas"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".livefreebrasil_cache.json")

# Configura encoding de saída para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

    elif sys.platform == "darwin":  # macOS
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
# TESTE E VALIDAÇÃO DE PROXIES
# -----------------------------------------------------------------------------

def test_socks5_proxy(host: str, port: int, timeout: float = 2.5) -> Optional[int]:
    """Testa handshake SOCKS5 até o discord.com:443."""
    try:
        t0 = time.time()
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"\x05\x01\x00")
        res = s.recv(2)
        if len(res) < 2 or res[0] != 5 or res[1] != 0:
            s.close()
            return None
            
        target = b"discord.com"
        port_num = 443
        req = b"\x05\x01\x00\x03" + bytes([len(target)]) + target + struct.pack(">H", port_num)
        s.sendall(req)
        res = s.recv(10)
        s.close()
        
        if len(res) >= 2 and res[0] == 5 and res[1] == 0:
            return round((time.time() - t0) * 1000)
    except Exception:
        return None
    return None


def test_http_proxy(host: str, port: int, timeout: float = 2.5) -> Optional[int]:
    """Testa túnel CONNECT HTTP/HTTPS até o discord.com:443."""
    try:
        t0 = time.time()
        s = socket.create_connection((host, int(port)), timeout=timeout)
        s.settimeout(timeout)
        req = "CONNECT discord.com:443 HTTP/1.1\r\nHost: discord.com:443\r\nUser-Agent: LiveFreeBrasil/1.0\r\n\r\n"
        s.sendall(req.encode("latin1"))
        res = s.recv(2048).decode("latin1", errors="ignore")
        s.close()
        if "200" in res:
            return round((time.time() - t0) * 1000)
    except Exception:
        return None
    return None


def check_tor_local() -> Optional[str]:
    """Verifica se o serviço Tor está rodando localmente nas portas padrões."""
    ports = [9050, 9150]
    for port in ports:
        ms = test_socks5_proxy("127.0.0.1", port, timeout=0.8)
        if ms is not None:
            return f"socks5://127.0.0.1:{port}"
    return None


def get_ip_country(ip: str) -> Optional[Dict[str, str]]:
    """Obtém país e cidade do IP via serviço geoip público leve."""
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,query"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                return {
                    "country": data.get("country", "Unknown"),
                    "code": data.get("countryCode", "??"),
                    "city": data.get("city", "")
                }
    except Exception:
        pass
    return None


def fetch_free_proxies() -> List[Tuple[str, str, int]]:
    """Baixa listas públicas de proxies gratuitas SOCKS5 e HTTP em paralelo."""
    candidates = []
    
    urls = [
        ("socks5", "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks5&timeout=2000&country=all"),
        ("http", "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=2000&country=all&ssl=yes&anonymity=elite"),
        ("socks5", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"),
        ("http", "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"),
        ("socks5", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"),
    ]
    
    def fetch_url(entry):
        proto, url = entry
        items = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                for line in text.strip().splitlines():
                    line = line.strip()
                    if line and ":" in line and not line.startswith("#"):
                        parts = line.split(":")
                        if len(parts) >= 2 and parts[1].isdigit():
                            items.append((proto, parts[0], int(parts[1])))
        except Exception:
            pass
        return items

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_url, u) for u in urls]
        for f in as_completed(futures):
            candidates.extend(f.result())
            
    # Remove duplicadas mantendo ordem
    unique = []
    seen = set()
    for item in candidates:
        key = (item[0], item[1], item[2])
        if key not in seen:
            seen.add(key)
            unique.append(item)
            
    return unique


def find_working_non_br_proxy(max_workers: int = 30, candidate_limit: int = 150) -> Optional[Dict]:
    """Testa concorrentemente as proxies e retorna a melhor proxy não-BR com menor latência."""
    log_info("Buscando listas de proxies públicas (SOCKS5/HTTP)...")
    candidates = fetch_free_proxies()
    
    if not candidates:
        log_error("Não foi possível obter a lista de proxies públicas.")
        return None
        
    log_info(f"Testando {min(len(candidates), candidate_limit)} proxies em paralelo contra 'discord.com:443'...")
    
    tested_working = []
    
    def worker(item):
        proto, host, port = item
        if proto == "socks5":
            latency = test_socks5_proxy(host, port, timeout=2.0)
        else:
            latency = test_http_proxy(host, port, timeout=2.0)
            
        if latency is not None:
            return {"proto": proto, "host": host, "port": port, "latency": latency}
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, c) for c in candidates[:candidate_limit]]
        for f in as_completed(futures):
            res = f.result()
            if res:
                tested_working.append(res)
                if len(tested_working) >= 6 and min(p["latency"] for p in tested_working) < 600:
                    break

    if not tested_working:
        log_error("Nenhuma proxy pública respondeu com sucesso ao handshake do Discord.")
        return None
        
    tested_working.sort(key=lambda x: x["latency"])
    
    log_info("Identificando país das melhores proxies...")
    for p in tested_working:
        geo = get_ip_country(p["host"])
        if geo:
            country_code = geo.get("code", "")
            country_name = geo.get("country", "Unknown")
            if country_code and country_code.upper() != "BR":
                p["country"] = country_name
                p["country_code"] = country_code
                p["url"] = f"{p['proto']}://{p['host']}:{p['port']}"
                return p
        else:
            p["country"] = "Internacional"
            p["country_code"] = "??"
            p["url"] = f"{p['proto']}://{p['host']}:{p['port']}"
            return p
            
    return None


# -----------------------------------------------------------------------------
# CACHE DE PROXIES
# -----------------------------------------------------------------------------

def save_to_cache(proxy_info: Dict):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(proxy_info, f)
    except Exception:
        pass


def load_from_cache() -> Optional[Dict]:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            proto = data.get("proto", "socks5")
            host = data.get("host")
            port = data.get("port")
            if host and port:
                if proto == "socks5":
                    lat = test_socks5_proxy(host, port, timeout=1.8)
                else:
                    lat = test_http_proxy(host, port, timeout=1.8)
                if lat is not None:
                    data["latency"] = lat
                    return data
    except Exception:
        pass
    return None


def clear_cache():
    """Remove o arquivo de cache de proxies."""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# LAUNCH DO DISCORD (COM E SEM PROXY)
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
        log_info(f"Iniciando {Color.BOLD}{install['name']}{Color.RESET} com proxy...")
    else:
        # Modo normal (sem proxy)
        if sys.platform == "win32":
            if install["type"] == "updater":
                cmd = [install["path"], "--processStart", f"{install['folder']}.exe"]
            else:
                cmd = [install["path"]]
        else:
            cmd = [install["path"]]
        log_info(f"Iniciando {Color.BOLD}{install['name']}{Color.RESET} em modo NORMAL (conexão direta)...")
        
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
    """Desativa o bypass, limpa o cache e reinicia o Discord de forma padrão/normal."""
    log_warning("Desativando LiveFreeBrasil e restaurando Discord normal...")
    log_info("Encerrando instâncias ativas do Discord...")
    kill_discord_processes()
    time.sleep(1.0)
    
    log_info("Limpando cache de proxies...")
    clear_cache()
    
    installs = find_discord_installations()
    if installs:
        target = installs[0]
        launch_discord(target, proxy_url=None)
        print(f"\n{Color.GREEN}{Color.BOLD}[✓] Bypass desativado com sucesso!{Color.RESET}")
        print(f"{Color.WHITE}O Discord está rodando normalmente com a sua conexão direta padrão.{Color.RESET}\n")
    else:
        log_error("Nenhuma instalação do Discord encontrada para reiniciar.")


# -----------------------------------------------------------------------------
# CLI E MODO INTERATIVO
# -----------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="LiveFreeBrasil CLI — Inicia o Discord Desktop com proxy fora do Brasil para liberar Live e Câmera.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "-p", "--proxy",
        type=str,
        help="Especifica uma URL de proxy customizada (Ex: socks5://127.0.0.1:9050 ou http://1.2.3.4:8080)"
    )
    parser.add_argument(
        "-t", "--tor",
        action="store_true",
        help="Força o uso do Tor local (127.0.0.1:9050 ou 9150)"
    )
    parser.add_argument(
        "-a", "--auto",
        action="store_true",
        help="Modo automático: detecta Discord e rota de proxy sem perguntas"
    )
    parser.add_argument(
        "--disable", "--restore", "--normal",
        dest="disable",
        action="store_true",
        help="Desativa o bypass, limpa cache e reinicia o Discord normalmente sem proxy"
    )
    parser.add_argument(
        "-k", "--kill",
        action="store_true",
        help="Fecha todas as instâncias em execução do Discord antes de iniciar"
    )
    parser.add_argument(
        "--no-kill",
        action="store_true",
        help="Não fecha as instâncias abertas do Discord"
    )
    parser.add_argument(
        "-d", "--discord",
        type=str,
        help="Caminho manual para o executável do Discord"
    )
    parser.add_argument(
        "--list-proxies",
        action="store_true",
        help="Apenas lista e testa proxies públicas disponíveis e encerra"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"LiveFreeBrasil CLI v{VERSION}"
    )
    
    return parser.parse_args()


def interactive_menu(installs: List[Dict[str, str]]) -> str:
    """Menu principal intuitivo."""
    target_name = installs[0]["name"] if installs else "Discord"
    
    print(f"{Color.BOLD}Selecione a ação desejada:{Color.RESET}")
    print(f"  [1] {Color.GREEN}{Color.BOLD}Ativar Bypass (100% Automático){Color.RESET} -> Detecta proxy internacional e abre o {target_name}")
    print(f"  [2] {Color.RED}{Color.BOLD}Desativar Bypass (Modo Normal){Color.RESET} -> Limpa configurações e abre o Discord sem proxy")
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
            else:
                log_error("Opção inválida.")
        except ValueError:
            log_error("Digite um número válido.")


def resolve_proxy(proxy_arg: Optional[str], force_tor: bool) -> Optional[Dict]:
    """Obtém e valida a proxy de forma rápida e automática."""
    # 1. Proxy manual direta
    if proxy_arg:
        url = proxy_arg if "://" in proxy_arg else f"http://{proxy_arg}"
        log_info(f"Usando proxy manual especificada: {Color.BOLD}{url}{Color.RESET}")
        return {"url": url, "country": "Manual", "latency": 0}

    # 2. Tor local forçado
    if force_tor:
        log_info("Verificando conexão com o serviço Tor local...")
        tor_url = check_tor_local()
        if tor_url:
            log_success(f"Tor detectado e conectado em: {tor_url}")
            return {"url": tor_url, "country": "Rede Tor (Anônimo)", "latency": 50}
        else:
            log_error("Tor local não foi encontrado nas portas 9050 ou 9150.")
            log_info("Dica: Inicie o serviço 'tor.exe' ou abra o 'Tor Browser' antes de usar essa opção.")
            return None

    # 3. Tenta Tor local automaticamente se disponível
    tor_url = check_tor_local()
    if tor_url:
        log_success(f"Tor local detectado automaticamente: {Color.BOLD}{tor_url}{Color.RESET}")
        return {"url": tor_url, "country": "Rede Tor", "latency": 50}

    # 4. Tenta Cache recente
    cached = load_from_cache()
    if cached:
        log_success(f"Proxy recuperada do cache: {Color.BOLD}{cached['url']}{Color.RESET} ({cached.get('country', 'Não-BR')}, {cached['latency']}ms)")
        return cached

    # 5. Busca e testa proxies públicas
    log_info("Buscando proxy pública fora do Brasil com baixa latência...")
    found = find_working_non_br_proxy()
    if found:
        log_success(f"Proxy encontrada: {Color.BOLD}{found['url']}{Color.RESET} [{found.get('country', 'Global')}] (Ping: {found['latency']}ms)")
        save_to_cache(found)
        return found

    return None


def main():
    if sys.platform == "win32":
        os.system("")

    print_banner()
    args = parse_args()

    # Modo Desativar Bypass
    if args.disable:
        disable_bypass()
        return

    # Modo apenas listar proxies
    if args.list_proxies:
        p = find_working_non_br_proxy(candidate_limit=150)
        if p:
            log_success(f"Melhor proxy ativa: {p['url']} - País: {p.get('country')} - Latência: {p['latency']}ms")
        return

    # 1. Localiza Discord automaticamente
    installs = find_discord_installations()
    selected_install = None

    if args.discord:
        if os.path.exists(args.discord):
            selected_install = {"name": "Discord Custom", "type": "direct", "path": args.discord, "folder": "Discord"}
        else:
            log_error(f"O caminho do Discord fornecido não existe: {args.discord}")
            sys.exit(1)
    elif installs:
        selected_install = installs[0]
    else:
        log_error("Nenhuma instalação do Discord foi detectada automaticamente.")
        custom = input("Por favor, digite o caminho completo para o Discord.exe: ").strip().strip('"')
        if os.path.exists(custom):
            selected_install = {"name": "Discord", "type": "direct", "path": custom, "folder": "Discord"}
        else:
            log_error("Caminho inválido. Encerrando.")
            sys.exit(1)

    # 2. Modo de execução
    force_tor = args.tor
    manual_proxy_url = args.proxy

    if not args.auto and not args.proxy and not args.tor and not args.kill:
        # Menu interativo intuitivo
        action = interactive_menu(installs)
        if action == "disable":
            disable_bypass()
            return
        elif action == "tor":
            force_tor = True
        elif action == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Digite o endereço da proxy (ex: socks5://127.0.0.1:9050): {Color.RESET}").strip()

    # 3. Encerra instâncias antigas
    if not args.no_kill:
        log_info("Encerrando instâncias antigas do Discord para aplicar a nova sessão...")
        kill_discord_processes()
        time.sleep(1.0)

    # 4. Resolve proxy automaticamente
    proxy_data = resolve_proxy(manual_proxy_url, force_tor=force_tor)
    
    if not proxy_data:
        log_error("Não foi possível obter uma proxy funcional fora do Brasil.")
        log_info("Tente abrir o Tor Browser antes de iniciar ou use uma proxy manual.")
        sys.exit(1)

    # 5. Inicia o Discord com a proxy
    print("-" * 66, flush=True)
    log_info(f"Discord detectado: {Color.BOLD}{selected_install['name']}{Color.RESET} ({selected_install['path']})")
    log_info(f"Proxy Server: {Color.GREEN}{Color.BOLD}{proxy_data['url']}{Color.RESET} ({proxy_data.get('country', 'Internacional')})")
    print("-" * 66, flush=True)
    
    launch_discord(selected_install, proxy_data["url"])
    
    print(f"\n{Color.GREEN}{Color.BOLD}Tudo pronto!{Color.RESET} O Discord iniciará sua sessão com IP internacional.", flush=True)
    print(f"{Color.DIM}Quando o Discord abrir, entre num canal de voz e as transmissões de tela (Live) e Câmera estarão liberadas.{Color.RESET}\n", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}[!] Operação cancelada pelo usuário.{Color.RESET}", flush=True)
        sys.exit(0)
