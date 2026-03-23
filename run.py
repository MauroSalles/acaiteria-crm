#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servidor Flask para Açaiteria CRM
Executa a aplicação em modo desenvolvimento local
ou como entry-point para deploy na nuvem.

Local:   python run.py
Nuvem:   gunicorn backend.app:app (via Procfile)
"""

import sys
import os
import socket
import subprocess
import platform

# Adicionar o caminho do projeto ao path do Python
projeto_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, projeto_root)

# Importar a aplicação
from backend.app import app, db


def obter_ip_local():
    """Descobre o IP da rede local (Wi-Fi/Ethernet)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def abrir_porta_firewall(porta):
    """Tenta abrir a porta no Firewall do Windows para acesso na rede local."""
    if platform.system() != "Windows":
        return
    try:
        nome_regra = f"AcaiteriaCRM-porta-{porta}"
        # Verifica se regra já existe
        check = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", f"name={nome_regra}"],
            capture_output=True, text=True
        )
        if nome_regra in check.stdout:
            return  # Regra já existe
        # Cria regra de entrada
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={nome_regra}", "dir=in", "action=allow",
             "protocol=TCP", f"localport={porta}"],
            capture_output=True, text=True
        )
        print(f"  Regra de firewall '{nome_regra}' criada com sucesso!")
    except Exception:
        print(f"  [!] Nao foi possivel abrir porta {porta} no firewall.")
        print(f"      Execute como Administrador ou abra manualmente.")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    ip_local = obter_ip_local()

    # Criar contexto de aplicação
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        print("\n" + "=" * 60)
        print("  ACAITERIA CRM - SERVIDOR INICIANDO")
        print("=" * 60)
        print("\n  Banco de dados inicializado!")
        print(f"\n  Este computador: http://localhost:{port}")
        print(f"  Celular/Rede:    http://{ip_local}:{port}")
        print(f"  Docs API:        http://localhost:{port}/api/docs")
        print("\n  Pressione CTRL+C para parar o servidor")
        print("=" * 60 + "\n")

    # Tentar abrir porta no firewall do Windows
    abrir_porta_firewall(port)

    # Iniciar servidor
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n  Servidor encerrado pelo usuario.")
    except Exception as erro:
        print(f"\n  Erro ao iniciar servidor:\n{erro}")
        sys.exit(1)
