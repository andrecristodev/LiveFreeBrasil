# 🚀 LiveFreeBrasil — Desbloqueio de Transmissão de Tela & Câmera no Discord (Brasil)

Ferramenta de código aberto para **Windows, Linux e macOS** que restaura as **transmissões de tela (Go Live), visualização de streams de amigos e Câmera** no Discord para contas brasileiras diretamente pelo terminal ou com **1 clique**.

---

## ⬇️ Download Direto (Executável Windows)

Se você não quer usar linha de comando ou não tem Python, baixe o executável pronto para uso:

👉 **[Baixar LiveFreeBrasil v2.5.0 (Última Versão Oficial)](https://github.com/andrecristodev/LiveFreeBrasil/releases/latest)**

- **`LiveFreeBrasil.exe`**: Executável único de 1 clique atualizado.
- **`LiveFreeBrasil-v2.5.0-windows-x64.zip`**: Pacote completo zipado.

Basta dar dois cliques no `.exe` baixado e ele faz tudo sozinho em segundo plano!

---

## 🎯 Recursos & Destaques da Versão 2.5.0

- 🧅 **Motor Tor 100% Autônomo com Auto-Cura**: Localiza ou baixa o motor oficial do Tor automaticamente. Valida caminhos de arquivos de inicialização para evitar qualquer erro de boot no Windows.
- 🛡️ **Sistema Anti-Fechamento da Janela**: O programa nunca fecha a janela do prompt repentinamente em caso de erro, permitindo ler mensagens e instruções na tela.
- ⚡ **Pool Dinâmico de +100 Proxies Internacionais**: Caso a rede local do usuário bloqueie o Tor, o LiveFreeBrasil busca e testa instantaneamente dezenas de proxies internacionais públicas em paralelo com fallback automático.
- 🩺 **Sistema de Diagnóstico & Logs (`--diag`)**: Ferramenta embutida para testar Gateway, TLS, IP de saída e latência, salvando histórico detalhado em `%LOCALAPPDATA%\LiveFreeBrasil\livefreebrasil.log`.
- 🛑 **Encerramento Forçado Anti-Lock**: Garante que todas as instâncias zumbis do Discord sejam encerradas antes da inicialização para repassar 100% dos argumentos de rede ao processo raiz.
- 🎥 **Fix do Erro 2012 e Streams de Amigos**: O tráfego de sinalização RTC (`*.discord.media`) e WebSockets conecta perfeitamente para permitir tanto transmitir quanto assistir à transmissão de outras pessoas na chamada sem tela preta ou ícone `!`.
- 🧹 **Auto-Limpeza de GPU & Cache**: Limpa caches corrompidos de renderização do Electron que causavam telas pretas no Discord.
- 🛑 **Desativação Limpa em 1 Clique**: Desative o bypass a qualquer momento com [`Desativar_LiveFreeBrasil.bat`](Desativar_LiveFreeBrasil.bat) ou pela opção do menu, encerrando o serviço e restaurando o Discord na sua internet normal.

---

## 📌 Como o LiveFreeBrasil funciona

O Discord valida a região geográfica do usuário durante o handshake inicial do Gateway WebSocket (`wss://gateway.discord.gg`). Se a conexão for iniciada sob um IP internacional, todos os recursos de transmissão de tela (Go Live), câmeras e visualização de streams são **100% liberados**.

O **LiveFreeBrasil**:
1. Localiza suas instalações do Discord automaticamente (Stable, Canary, PTB, Development ou Vesktop).
2. Encerra qualquer processo residual para evitar o single-instance lock do Chromium.
3. Inicia o motor de conexão internacional segura em segundo plano.
4. Valida a rota antes de abrir o Discord, evitando qualquer erro de timeout (`ERR_TIMED_OUT`) ou carregamento infinito.
5. Inicia o Discord nativamente liberado com qualidade máxima (1080p 60fps).

---

## 💻 Como Usar

### 1. Iniciar com Bypass (100% Automático)
Dê dois cliques no executável ou arquivo bat:
```
LiveFreeBrasil.exe
```
ou
```
LiveFreeBrasil.bat
```

---

### 2. Desativar Bypass e Voltar ao Discord Normal
Dê dois cliques no arquivo:
```
Desativar_LiveFreeBrasil.bat
```
*(ou execute `LiveFreeBrasil.exe --disable`)*

---

### 3. Testar Conexão e Ver Logs (Diagnóstico)
```bash
LiveFreeBrasil.exe --diag
```

---

### 4. No Terminal (Modo Interativo com Menu)
```bash
python livefreebrasil.py
# ou
.\LiveFreeBrasil.bat
```

Menu interativo:
```text
Selecione a ação desejada:
  [1] Ativar Bypass (Motor Invisível - 100% Automático)
  [2] Desativar Bypass (Modo Normal) -> Abre direto sem proxy
  [3] Limpar Cache Gráfico (Reparar Tela Preta)
  [4] Ver Diagnóstico & Logs de Conexão
  [5] Informar Proxy Manualmente
  [6] Sair
```

---

## 📁 Arquivos do Projeto

- [`LiveFreeBrasil.exe`](https://github.com/andrecristodev/LiveFreeBrasil/releases/latest): Executável único compilado de 1 clique.
- [`LiveFreeBrasil.bat`](LiveFreeBrasil.bat): Script automatizado para Windows.
- [`Desativar_LiveFreeBrasil.bat`](Desativar_LiveFreeBrasil.bat): Desativa o bypass e restaura o Discord normal.
- [`livefreebrasil.py`](livefreebrasil.py): Código-fonte CLI principal em Python.
- [`Criar_Atalho_Area_de_Trabalho.bat`](Criar_Atalho_Area_de_Trabalho.bat): Cria um ícone de atalho na sua Área de Trabalho.
- [`LICENSE`](LICENSE): Licença aberta do projeto.
