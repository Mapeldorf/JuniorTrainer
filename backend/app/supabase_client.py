from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_anon_client() -> Client:
    """Cliente con la clave anon: solo para validar el JWT de un usuario."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_admin_client() -> Client:
    """Cliente con la clave service_role: salta RLS y da acceso a la Admin API
    (invitar alumnos, etc). Solo lo usa el backend, nunca el frontend."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
