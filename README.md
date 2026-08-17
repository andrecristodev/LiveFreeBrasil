# 🚀 LiveFreeBrasil CLI — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil) via Terminal

Ferramenta de linha de comando para **Windows, Linux e macOS** que restaura as **transmissões de tela (Lives) e Câmera** no Discord para contas brasileiras diretamente pelo terminal ou com **1 clique**.

---

## 👑 Créditos

- **Criador:** `@tadalas` no Discord

---

## ⬇️ Download Direto (Executável Windows)

Se você não quer usar linha de comando ou não tem Python, baixe o executável pronto para uso:

👉 **[Baixar LiveFreeBrasil.exe (Release v1.1.0)](https://github.com/andrecristodev/LiveFreeBrasil/releases/latest)**

Basta dar dois cliques no `.exe` baixado e ele faz tudo sozinho!

---

## 📌 Por que o bloqueio acontece e como o LiveFreeBrasil funciona

Em agosto de 2026, a ANPD determinou a suspensão das transmissões ao vivo (Lives) e câmeras no Discord para usuários no Brasil.

### Como o Discord valida a região:
1. O Discord verifica o país de origem **apenas no momento da autenticação e abertura do WebSocket do Gateway** (`wss://gateway.discord.gg`).
2. Se a sessão é iniciada sob um IP fora do Brasil (via proxy SOCKS5/HTTP ou Tor), os recursos de transmissão e câmera são **totalmente liberados**.
3. O tráfego de voz e mídia subsequente via UDP conecta diretamente sem restrições.
4. O `LiveFreeBrasil` localiza suas instalações do Discord automaticamente, obtém/testa uma proxy internacional ultra-rápida (ou conecta ao Tor local se disponível) e inicia o aplicativo com as flags nativas do Chromium/Electron (`--proxy-server="..."`).

---

## ⚡ Recursos do LiveFreeBrasil

- 🖱️ **Execução 100% Automática**: Detecta a pasta do Discord instalada e a melhor rota de proxy internacional sem precisar configurar nada.
- 🛑 **Sistema de Desativação em 1 Clique**: Desative o bypass a qualquer momento com [`Desativar_LiveFreeBrasil.bat`](Desativar_LiveFreeBrasil.bat) ou pela opção do menu, restaurando o Discord normal sem proxy.
- 📦 **Autoinstalação do Python**: Se o usuário não tiver Python instalado, o próprio `.bat` baixa e instala silenciosamente!
- 🔍 **Detecção Automática do Discord**: Encontra Discord Stable, Canary, PTB, Development e Vesktop instalados no sistema.
- 🧅 **Suporte a Tor Local**: Detecta automaticamente se o serviço Tor ou Tor Browser está rodando nas portas `9050` ou `9150`.
- 🌐 **Busca e Teste de Proxies Públicas**: Baixa listas de proxies SOCKS5/HTTP e testa o handshake real contra `discord.com:443` em paralelo, validando que o IP é de fora do Brasil.
- 💾 **Cache Inteligente**: Salva a última proxy funcional para que inicializações futuras sejam quase instantâneas.
- 🎯 **Totalmente Customizável**: Suporta proxies manuais, seleção de executáveis e modo interativo ou 100% automático.

---

## 💻 Como Usar

### 1. Iniciar com Bypass (100% Automático)
Dê dois cliques no arquivo:
```
LiveFreeBrasil.bat
```
*(ou execute `LiveFreeBrasil.exe --auto`)*

---

### 2. Desativar Bypass e Voltar ao Discord Normal
Dê dois cliques no arquivo:
```
Desativar_LiveFreeBrasil.bat
```
*(ou execute `LiveFreeBrasil.exe --disable`)*

---

### 3. No Terminal (Modo Interativo com Menu)
```bash
python livefreebrasil.py
# ou
.\livefreebrasil.bat
```

No menu você pode:
- **[1]** Ativar Bypass (100% Automático)
- **[2]** Desativar Bypass (Restaurar Discord normal)
- **[3]** Usar Tor Local
- **[4]** Informar Proxy Manualmente
- **[5]** Sair

---

## 📁 Arquivos do Projeto

- [`LiveFreeBrasil.bat`](LiveFreeBrasil.bat): Inicia o Discord com bypass 100% automático.
- [`Desativar_LiveFreeBrasil.bat`](Desativar_LiveFreeBrasil.bat): Desativa o bypass e restaura o Discord normal.
- [`livefreebrasil.py`](livefreebrasil.py): Script CLI principal em Python.
- [`livefreebrasil.bat`](livefreebrasil.bat): Wrapper CLI para Prompt de Comando.
- [`livefreebrasil.ps1`](livefreebrasil.ps1): Wrapper para PowerShell.
- [`Criar_Atalho_Area_de_Trabalho.bat`](Criar_Atalho_Area_de_Trabalho.bat): Cria um ícone de atalho na Área de Trabalho.
