"""Crea el primer tech lead (admin) del sistema.

No hay autorregistro: este script es la unica forma de dar de alta al primer
usuario. Crea la fila en auth.users con email_confirm=True y contrasena ya
puesta (no hace falta invitacion); el trigger on_auth_user_created crea el
Profile correspondiente con role='tech_lead'.

Uso:
    python -m scripts.seed_tech_lead --email tech@lead.com --name "Nombre" [--password ...]

Si no se pasa --password, se pide por entrada segura (getpass).
"""

import argparse
import getpass
import sys

from app.supabase_client import get_admin_client


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", default=None, help="Si se omite, se pide por entrada segura")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Contrasena del tech lead: ")
    if len(password) < 8:
        print("La contrasena debe tener al menos 8 caracteres.", file=sys.stderr)
        raise SystemExit(1)

    email = args.email.lower()

    response = get_admin_client().auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": args.name, "role": "tech_lead"},
        }
    )

    if response.user is None:
        print("No se ha podido crear el usuario.", file=sys.stderr)
        raise SystemExit(1)

    print(f"tech_lead creado: {email} (id {response.user.id})")


if __name__ == "__main__":
    main()
