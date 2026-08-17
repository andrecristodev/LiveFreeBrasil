# 🚀 LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal

Ferramenta de linha de comando para **Windows, Linux e macOS** que restaura as **transmissões de tela (Lives) e Câmera** no Discord para contas brasileiras diretamente pelo terminal ou com **1 clique**.

---

## 👑 Créditos

- **Criador:** `@tadalas` no Discord

---

## 📌 Por que o bloqueio acontece e como o LiveFreeBrasil funciona

Em agosto de 2026, a ANPD determinou a suspensão das transmissões ao vivo (Lives) e câmeras no Discord para usuários no Brasil.

### Como o Discord valida a região:
1. O Discord verifica o país de origem **apenas no momento da autenticação e abertura do WebSocket do Gateway** (`wss://gateway.discord.gg`).
2. Se a sessão é iniciada sob um IP fora do Brasil (via proxy SOCKS5/HTTP ou Tor), os recursos de transmissão e câmera são **totalmente liberados**.
3. O tráfego de voz e mídia subsequente via UDP conecta diretamente sem restrições.
4. O `LiveFreeBrasil` localiza suas instalações do Discord (Stable, Canary, PTB, Vesktop), obtém/testa uma proxy internacional ultra-rápida (ou conecta ao Tor local se disponível) e inicia o aplicativo com as flags nativas do Chromium/Electron (`--proxy-server="..."`).

---

## ⚡ Recursos do LiveFreeBrasil

- 🖱️ **Execução em 1 Clique**: Dê dois cliques em [`LiveFreeBrasil.bat`](LiveFreeBrasil.bat) e tudo é autoconfigurado.
- 📦 **Autoinstalação do Python**: Se o usuário não tiver Python instalado, o próprio script baixa e instala silenciosamente sem pedir nada!
- 🔍 **Detecção Automática do Discord**: Encontra Discord Stable, Canary, PTB, Development e Vesktop instalados no sistema.
- 🧅 **Suporte a Tor Local**: Detecta automaticamente se o serviço Tor ou Tor Browser está rodando nas portas `9050` ou `9150`.
- 🌐 **Busca e Teste de Proxies Públicas**: Baixa listas de proxies SOCKS5/HTTP e testa o handshake real contra `discord.com:443` em paralelo, validando que o IP é de fora do Brasil.
- 💾 **Cache Inteligente**: Salva a última proxy funcional para que inicializações futuras sejam quase instantâneas.
- 🎯 **Totalmente Customizável**: Suporta proxies manuais, seleção de executáveis e modo interativo ou 100% automático.
- 🚀 **Zero Dependências Manuais**: O script usa apenas módulos nativos (não precisa de nenhum `pip install`).

---

## 💻 Como Usar

### 1. Dois Cliques (Modo Automático)
Dê dois cliques no arquivo:
```
LiveFreeBrasil.bat
```

---

### 2. No Terminal (Modo Interativo com Menu)
```bash
python livefreebrasil.py
# ou
.\livefreebrasil.bat
```

---

### 3. Modo Direto via Linha de Comando
```bash
# 100% Automático
python livefreebrasil.py --auto

# Forçar uso do Tor local
python livefreebrasil.py --tor

# Usar proxy personalizada
python livefreebrasil.py --proxy socks5://127.0.0.1:9050

# Apenas listar proxies ativas
python livefreebrasil.py --list-proxies
```

---

## 📁 Arquivos do Projeto

- [`LiveFreeBrasil.bat`](LiveFreeBrasil.bat): Executável de 1 clique para Windows.
- [`livefreebrasil.py`](livefreebrasil.py): Script CLI principal em Python.
- [`livefreebrasil.bat`](livefreebrasil.bat): Wrapper CLI para CMD/Prompt.
- [`livefreebrasil.ps1`](livefreebrasil.ps1): Wrapper para PowerShell.
- [`Criar_Atalho_Area_de_Trabalho.bat`](Criar_Atalho_Area_de_Trabalho.bat): Cria um ícone de atalho na Área de Trabalho.
