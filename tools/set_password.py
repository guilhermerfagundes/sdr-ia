"""
Cria/atualiza o usuário e senha de login do painel.

Uso interativo (recomendado):
    python tools/set_password.py

Uso direto:
    python tools/set_password.py --user admin --password "minhaSenha"

O script:
  1. Gera o hash seguro da senha (bcrypt).
  2. Salva em auth_config.yaml (usado quando você roda local).
  3. Imprime o bloco pronto para colar nos "Secrets" do Streamlit Cloud (nuvem).
"""
from __future__ import annotations

import argparse
import getpass
import secrets as pysecrets
import sys
from pathlib import Path

import yaml
from streamlit_authenticator.utilities.hasher import Hasher

AUTH_FILE = Path(__file__).resolve().parents[1] / "auth_config.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Define usuário e senha do painel SDR IA")
    parser.add_argument("--user", help="nome de usuário para login")
    parser.add_argument("--password", help="senha (se omitida, pergunta de forma segura)")
    parser.add_argument("--name", default="Administrador", help="nome exibido no painel")
    args = parser.parse_args()

    user = args.user or input("Usuário: ").strip()
    if not user:
        print("Usuário não pode ser vazio.")
        sys.exit(1)
    senha = args.password or getpass.getpass("Senha: ")
    if not senha:
        print("Senha não pode ser vazia.")
        sys.exit(1)

    hashed = Hasher([senha]).generate()[0]
    cookie_key = pysecrets.token_hex(16)

    data = {
        "credentials": {
            "usernames": {
                user: {"name": args.name, "password": hashed, "email": ""}
            }
        },
        "cookie": {"name": "sdr_ia_auth", "key": cookie_key, "expiry_days": 30},
    }

    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"\n✅ Login configurado para o usuário '{user}'.")
    print(f"   Arquivo local criado: {AUTH_FILE}")
    print("\n----- Para a NUVEM (Streamlit Cloud) -----")
    print("Cole o bloco abaixo em 'Settings → Secrets' do app no Streamlit Cloud:\n")
    print(f'[auth.credentials.usernames.{user}]')
    print(f'name = "{args.name}"')
    print(f'password = "{hashed}"')
    print('email = ""')
    print('\n[auth.cookie]')
    print('name = "sdr_ia_auth"')
    print(f'key = "{cookie_key}"')
    print("expiry_days = 30")
    print("\n(E não esqueça de adicionar também as linhas DATABASE_URL e GOOGLE_PLACES_API_KEY.)")


if __name__ == "__main__":
    main()
