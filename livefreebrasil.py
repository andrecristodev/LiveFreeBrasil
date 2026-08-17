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

VERSION = "1.0.0"
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
# DETECÇÃO DE INSTALAÇÕES DO DISCORD
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
    """Finaliza processos em execução do Discord para permitir reinício limpo com proxy."""
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
        
    # Ordena por menor latência
    tested_working.sort(key=lambda x: x["latency"])
    
    # Filtra por país != BR
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


# -----------------------------------------------------------------------------
# LAUNCH DO DISCORD
# -----------------------------------------------------------------------------

def launch_discord(install: Dict[str, str], proxy_url: str):
    """Executa o Discord com os argumentos de proxy necessários."""
    proxy_arg = f'--proxy-server={proxy_url}'
    
    cmd = []
    if sys.platform == "win32":
        if install["type"] == "updater":
            cmd = [install["path"], "--processStart", f"{install['folder']}.exe", "--process-args", proxy_arg]
        else:
            cmd = [install["path"], proxy_arg]
    else:
        cmd = [install["path"], proxy_arg]
        
    log_info(f"Executando: {Color.DIM}{' '.join(cmd)}{Color.RESET}")
    
    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, close_fds=True)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        
        log_success(f"{install['name']} iniciado com sucesso através da proxy!")
    except Exception as e:
        log_error(f"Falha ao iniciar o Discord: {e}")


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
        help="Modo automático: detecta Tor, cache ou busca proxy pública sem perguntar"
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


def interactive_menu(installs: List[Dict[str, str]]) -> Tuple[Dict[str, str], str, bool]:
    """Menu interativo quando nenhuma flag específica foi passada."""
    print(f"{Color.BOLD}1. Selecione a versão do Discord instalada:{Color.RESET}")
    for idx, inst in enumerate(installs):
        print(f"  [{idx + 1}] {Color.GREEN}{inst['name']}{Color.RESET} ({Color.DIM}{inst['path']}{Color.RESET})")
    print(f"  [{len(installs) + 1}] Informar caminho personalizado...")
    
    while True:
        try:
            choice = input(f"\n{Color.CYAN}Opção [1-{len(installs) + 1}] (padrão: 1): {Color.RESET}").strip()
            if not choice:
                selected_install = installs[0]
                break
            c_int = int(choice)
            if 1 <= c_int <= len(installs):
                selected_install = installs[c_int - 1]
                break
            elif c_int == len(installs) + 1:
                custom_path = input("Digite o caminho completo para o executável do Discord: ").strip().strip('"')
                if os.path.exists(custom_path):
                    selected_install = {"name": "Discord Personalizado", "type": "direct", "path": custom_path, "folder": "Discord"}
                    break
                else:
                    log_error("Caminho não encontrado. Tente novamente.")
            else:
                log_error("Opção inválida.")
        except ValueError:
            log_error("Digite um número válido.")

    print(f"\n{Color.BOLD}2. Escolha o método de conexão proxy:{Color.RESET}")
    print(f"  [1] {Color.GREEN}Automático{Color.RESET} (Tor local se ativo > Cache rápido > Proxies públicas gratuitas)")
    print(f"  [2] {Color.CYAN}Tor Local{Color.RESET} (socks5://127.0.0.1:9050 ou 9150)")
    print(f"  [3] {Color.YELLOW}Buscar Nova Proxy Pública Testada{Color.RESET} (Não-BR)")
    print(f"  [4] {Color.MAGENTA}Digitar Proxy Manualmente{Color.RESET} (Ex: socks5://ip:porta ou http://ip:porta)")

    while True:
        try:
            p_choice = input(f"\n{Color.CYAN}Opção [1-4] (padrão: 1): {Color.RESET}").strip()
            if not p_choice or p_choice == "1":
                proxy_mode = "auto"
                break
            elif p_choice == "2":
                proxy_mode = "tor"
                break
            elif p_choice == "3":
                proxy_mode = "public"
                break
            elif p_choice == "4":
                proxy_mode = "manual"
                break
            else:
                log_error("Opção inválida.")
        except ValueError:
            log_error("Digite um número válido.")

    kill_choice = input(f"\n{Color.CYAN}Deseja encerrar instâncias anteriores do Discord? [S/n] (padrão: S): {Color.RESET}").strip().lower()
    should_kill = kill_choice != "n"

    return selected_install, proxy_mode, should_kill


def resolve_proxy(proxy_arg: Optional[str], force_tor: bool, force_public: bool = False) -> Optional[Dict]:
    """Obtém e valida a proxy de acordo com a estratégia solicitada."""
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

    # 3. Tenta Tor local silenciosamente se modo automático
    if not force_public:
        tor_url = check_tor_local()
        if tor_url:
            log_success(f"Tor local detectado automaticamente: {Color.BOLD}{tor_url}{Color.RESET}")
            return {"url": tor_url, "country": "Rede Tor", "latency": 50}

        # 4. Tenta Cache recente
        cached = load_from_cache()
        if cached:
            log_success(f"Proxy recente recuperada do cache: {Color.BOLD}{cached['url']}{Color.RESET} ({cached.get('country', 'Não-BR')}, {cached['latency']}ms)")
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

    # Modo apenas listar proxies
    if args.list_proxies:
        p = find_working_non_br_proxy(candidate_limit=150)
        if p:
            log_success(f"Melhor proxy ativa: {p['url']} - País: {p.get('country')} - Latência: {p['latency']}ms")
        return

    # 1. Localiza Discord
    installs = find_discord_installations()
    selected_install = None

    if args.discord:
        if os.path.exists(args.discord):
            selected_install = {"name": "Discord Custom", "type": "direct", "path": args.discord, "folder": "Discord"}
        else:
            log_error(f"O caminho do Discord fornecido não existe: {args.discord}")
            sys.exit(1)
    elif not installs:
        log_error("Nenhuma instalação do Discord foi detectada automaticamente.")
        custom = input("Por favor, digite o caminho completo para o Discord.exe: ").strip().strip('"')
        if os.path.exists(custom):
            selected_install = {"name": "Discord", "type": "direct", "path": custom, "folder": "Discord"}
        else:
            log_error("Caminho inválido. Encerrando.")
            sys.exit(1)

    # 2. Determina configurações de execução
    should_kill = args.kill
    proxy_mode = "auto"
    manual_proxy_url = args.proxy

    if not args.auto and not args.proxy and not args.tor and not args.no_kill and not args.kill and not args.discord:
        # Modo interativo
        selected_install, proxy_mode, should_kill = interactive_menu(installs)
        if proxy_mode == "manual":
            manual_proxy_url = input(f"{Color.CYAN}Digite o endereço da proxy (ex: socks5://127.0.0.1:9050): {Color.RESET}").strip()
    else:
        if not selected_install:
            selected_install = installs[0]
        if not args.no_kill:
            should_kill = True

    # 3. Encerra instâncias antigas se solicitado
    if should_kill:
        log_info("Encerrando instâncias antigas do Discord para aplicar a proxy no boot...")
        kill_discord_processes()
        time.sleep(1.0)

    # 4. Resolve a proxy
    force_tor = (args.tor or proxy_mode == "tor")
    force_public = (proxy_mode == "public")
    
    proxy_data = resolve_proxy(manual_proxy_url, force_tor=force_tor, force_public=force_public)
    
    if not proxy_data:
        log_error("Não foi possível obter uma proxy funcional fora do Brasil.")
        log_info("Tente rodar com o Tor aberto (`--tor`) ou passe uma proxy manual (`--proxy socks5://...`)")
        sys.exit(1)

    # 5. Inicia o Discord com a proxy
    print("-" * 66, flush=True)
    log_info(f"Alvo: {Color.BOLD}{selected_install['name']}{Color.RESET}")
    log_info(f"Proxy Server: {Color.GREEN}{Color.BOLD}{proxy_data['url']}{Color.RESET} ({proxy_data.get('country', 'Fora do Brasil')})")
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
