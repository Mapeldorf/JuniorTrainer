"""Verificacion manual (sin servidor HTTP) de los ajustes de backend del
change frontend-tech-lead-ejercicios (tareas 1.2-1.6): listar generaciones
pendientes (excluyendo las `done` y las `error`), cerrar la revision de una generacion
lista (y el rechazo de cerrar una en curso o en error), guardar un
candidato con una respuesta esperada editada (y sin ella), que el
listado de ejercicios guardados incluya las tecnologias y el repositorio
de su generacion incluso cuando esa generacion ya esta `done`, y (change
`eliminar-generaciones-por-revisar`) eliminar una generacion `ready` con
sus candidatos (y el rechazo de una en curso, una con ejercicios guardados
y una inexistente).

Llama directamente a las funciones de los routers (sin levantar un
servidor HTTP) contra el proyecto Supabase REAL configurado en el .env de
la raiz -- mismo patron que verify_valoracion_respuestas.py y
verify_bloques_asignaciones.py. No hace falta ningun agente de generacion
arrancado: las generaciones y sus candidatos se insertan directamente en
la base de datos (igual que ya hacia verify_bloques_asignaciones.py con
sus ejercicios), no a traves de `POST /generations` -- lo que se prueba
aqui es el listado/cierre/guardado, no la orquestacion de agentes (eso ya
lo cubre verify_generation_e2e.py).

Crea sus propias generaciones y ejercicios de prueba, marcados con un tag
unico, y los borra al terminar, incluso si una comprobacion falla.

Necesita que ya exista al menos un profile con role='tech_lead' (lo crea
seed_tech_lead.py si no hay ninguno todavia).

Uso (desde backend/, con el venv del backend activo):
    python -m scripts.verify_ejercicios_tech_lead

Con `--full` (tarea 1.6) anade, al final, el flujo completo de verdad con
agentes reales: generar sin repositorio (`POST /generations`, vía
`run_generation` directamente, mismo patron que verify_generation_e2e.py),
esperar a que quede `ready`, revisarla (`GET /generations/{id}`), guardar
un candidato con una respuesta esperada editada, cerrar la revision, y
confirmar que desaparece de pendientes y que el guardado aparece en
`GET /exercises`. Necesita los agentes web y de ejercicios arrancados
(mismas dos terminales que verify_generation_e2e.py, con
AGENT_WEB_URL/AGENT_EXERCISES_URL apuntando a localhost):
    AGENT_WEB_URL=http://127.0.0.1:8010/ AGENT_EXERCISES_URL=http://127.0.0.1:8012/ \
    python -m scripts.verify_ejercicios_tech_lead --full
"""

import asyncio
import sys
import uuid

from fastapi import HTTPException

import app.orchestrator as orchestrator
from app.deps import require_tech_lead
from app.routers import exercises, generations, technologies
from app.schemas.exercise import SaveExerciseRequest
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

TAG = f"verify-ejercicios-{uuid.uuid4().hex[:8]}"


async def main() -> None:
    admin = get_admin_client()

    tech_lead_rows = (
        admin.table("profile")
        .select("id, email, name")
        .eq("role", "tech_lead")
        .limit(1)
        .execute()
        .data
    )
    if not tech_lead_rows:
        raise SystemExit(
            "no hay ningun profile con role='tech_lead' todavia -- "
            "crea uno con `python -m scripts.seed_tech_lead` primero"
        )
    tech_lead_row = tech_lead_rows[0]
    tech_lead = Profile(
        id=tech_lead_row["id"],
        email=tech_lead_row["email"],
        name=tech_lead_row["name"],
        role="tech_lead",
    )
    print(f"usando tech_lead: {tech_lead.email} ({tech_lead.id})")

    created_generation_ids: list[str] = []
    created_exercise_ids: list[str] = []

    try:
        # --- change catalogo-tecnologias (tarea 2.2): GET /technologies ---
        catalog = await technologies.list_technologies(_profile=tech_lead)
        catalog_names = {t.name for t in catalog}
        expected_catalog = {
            "Angular",
            "TypeScript",
            "RxJS",
            "NgRx",
            "Angular Material",
            "Angular CDK",
            "Angular Router",
            "Angular Forms",
            "Angular CLI",
            "Jasmine",
        }
        assert expected_catalog <= catalog_names, (
            f"faltan tecnologias del catalogo: {expected_catalog - catalog_names}"
        )
        print(f"OK: 2.2 GET /technologies devuelve el catalogo ({len(catalog)} tecnologias)")

        student_profile = Profile(
            id="00000000-0000-0000-0000-000000000000",
            email="student@example.com",
            name="student",
            role="student",
        )
        try:
            await require_tech_lead(profile=student_profile)
            raise AssertionError("GET /technologies deberia rechazar a un alumno (403)")
        except HTTPException as exc:
            assert exc.status_code == 403
        print("OK: 2.2 GET /technologies rechaza a un alumno (403)")

        # --- 1.2: GET /generations solo devuelve generating/ready ---
        gen_ready = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Git, Python ({TAG})",
                    "kind": "knowledge",
                    "status": "ready",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_ready["id"])

        gen_done = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Docker ({TAG})",
                    "kind": "knowledge",
                    "status": "done",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_done["id"])

        gen_error = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Rust ({TAG})",
                    "kind": "knowledge",
                    "status": "error",
                    "error_message": "fallo de prueba",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_error["id"])

        pending = await generations.list_pending_generations(_profile=tech_lead)
        pending_ids = {g.id for g in pending}
        assert gen_ready["id"] in pending_ids, "la generacion ready deberia aparecer en pendientes"
        assert gen_error["id"] not in pending_ids, "la generacion error NO deberia aparecer en pendientes"
        assert gen_done["id"] not in pending_ids, "la generacion done NO deberia aparecer en pendientes"
        print("OK: 1.2 GET /generations devuelve ready y excluye error/done")

        # --- 1.3: POST /generations/{id}/close ---
        try:
            await generations.close_generation(gen_error["id"], _profile=tech_lead)
            raise AssertionError("cerrar una generacion en error deberia rechazarse")
        except HTTPException as exc:
            assert exc.status_code == 409

        gen_generating = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Go ({TAG})",
                    "kind": "knowledge",
                    "status": "generating",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_generating["id"])
        try:
            await generations.close_generation(gen_generating["id"], _profile=tech_lead)
            raise AssertionError("cerrar una generacion generating deberia rechazarse")
        except HTTPException as exc:
            assert exc.status_code == 409
        print("OK: 1.3 cerrar una generacion generating/error se rechaza (409)")

        # candidato sin guardar en gen_ready, para comprobar que cerrar
        # funciona igual con candidatos sin guardar (requisito "Cerrar la
        # revision con candidatos sin guardar")
        unsaved_candidate = (
            admin.table("exercise")
            .insert(
                {
                    "generation_id": gen_ready["id"],
                    "type": "knowledge",
                    "name": f"sin guardar {TAG}",
                    "statement": f"pregunta sin guardar {TAG}",
                    "code": [],
                    "expected_answer": "no se guarda",
                    "saved": False,
                }
            )
            .execute()
            .data[0]
        )
        created_exercise_ids.append(unsaved_candidate["id"])

        closed = await generations.close_generation(gen_ready["id"], _profile=tech_lead)
        assert closed.status == "done"
        pending_after = await generations.list_pending_generations(_profile=tech_lead)
        assert gen_ready["id"] not in {g.id for g in pending_after}
        print(
            "OK: 1.3 cerrar una generacion ready funciona incluso con candidatos sin "
            "guardar, y desaparece de pendientes"
        )

        # --- 1.4: POST /exercises/{id}/save con/sin expected_answer ---
        # (se guardan candidatos de gen_ready, que ya esta `done` -- guardar
        # no depende del estado de la generacion, solo del propio ejercicio)
        candidate_a = (
            admin.table("exercise")
            .insert(
                {
                    "generation_id": gen_ready["id"],
                    "type": "knowledge",
                    "name": f"pregunta A {TAG}",
                    "statement": f"pregunta A {TAG}",
                    "code": [],
                    "expected_answer": "respuesta original A",
                    "saved": False,
                }
            )
            .execute()
            .data[0]
        )
        created_exercise_ids.append(candidate_a["id"])
        saved_without = await exercises.save_exercise(
            candidate_a["id"], body=None, _tech_lead=tech_lead
        )
        assert saved_without.expected_answer == "respuesta original A"
        print("OK: 1.4 guardar sin expected_answer conserva la respuesta original")

        candidate_b = (
            admin.table("exercise")
            .insert(
                {
                    "generation_id": gen_ready["id"],
                    "type": "knowledge",
                    "name": f"pregunta B {TAG}",
                    "statement": f"pregunta B {TAG}",
                    "code": [],
                    "expected_answer": "respuesta original B",
                    "saved": False,
                }
            )
            .execute()
            .data[0]
        )
        created_exercise_ids.append(candidate_b["id"])
        saved_with = await exercises.save_exercise(
            candidate_b["id"],
            body=SaveExerciseRequest(expected_answer="respuesta editada B"),
            _tech_lead=tech_lead,
        )
        assert saved_with.expected_answer == "respuesta editada B"
        print("OK: 1.4 guardar con expected_answer sustituye la respuesta original")

        # --- 1.5: GET /exercises incluye technologies/repo, incluso
        # con la generacion ya done ---
        all_page = await exercises.list_saved_exercises(
            type=None, q=TAG, page=1, page_size=None, _tech_lead=tech_lead
        )
        by_id = {e.id: e for e in all_page.items}
        assert candidate_a["id"] in by_id and candidate_b["id"] in by_id
        assert unsaved_candidate["id"] not in by_id, "un candidato sin guardar no debe listarse"
        item = by_id[candidate_a["id"]]
        assert item.technologies == ["Git", f"Python ({TAG})"], item.technologies
        assert item.repo is None
        print(
            f"OK: 1.5 GET /exercises incluye technologies ({item.technologies}) y "
            f"repo de una generacion que ya esta done"
        )

        # --- 1.4 (change paginacion-ejercicios-guardados): GET /exercises
        # paginado ---
        # Sin page_size el listado sigue devolviendo todos los coincidentes
        # (comportamiento que necesita la composicion de bloques).
        assert all_page.total == 2, all_page.total
        assert all_page.page == 1
        assert all_page.page_size == 2, all_page.page_size
        assert len(all_page.items) == 2, len(all_page.items)
        print("OK: 1.4 sin page_size GET /exercises devuelve todos los coincidentes con total")

        # Primera y segunda pagina de tamano 1: una fila cada una, mismo
        # total, y entre las dos cubren los dos ejercicios (sin solaparse).
        first = await exercises.list_saved_exercises(
            type=None, q=TAG, page=1, page_size=1, _tech_lead=tech_lead
        )
        second = await exercises.list_saved_exercises(
            type=None, q=TAG, page=2, page_size=1, _tech_lead=tech_lead
        )
        assert first.total == 2 and second.total == 2
        assert len(first.items) == 1 and len(second.items) == 1
        assert first.page_size == 1 and second.page_size == 1
        first_id = first.items[0].id
        second_id = second.items[0].id
        assert {first_id, second_id} == {candidate_a["id"], candidate_b["id"]}, (
            first_id,
            second_id,
        )
        print("OK: 1.4 paginar con page_size=1 reparte los coincidentes en paginas")

        # Una pagina mas alla de la ultima devuelve una lista vacia y el
        # total real de coincidencias.
        beyond = await exercises.list_saved_exercises(
            type=None, q=TAG, page=3, page_size=1, _tech_lead=tech_lead
        )
        assert beyond.items == [], beyond.items
        assert beyond.total == 2, beyond.total
        print("OK: 1.4 una pagina fuera de rango devuelve items vacios y el total real")

        # La paginacion respeta los filtros: un tipo sin coincidencias con
        # TAG da total 0 aunque existan coincidencias por texto.
        filtered = await exercises.list_saved_exercises(
            type="debug", q=TAG, page=1, page_size=1, _tech_lead=tech_lead
        )
        assert filtered.total == 0, filtered.total
        assert filtered.items == [], filtered.items
        print("OK: 1.4 el total y la pagina respetan el filtro por tipo")

        # --- change eliminar-generaciones-por-revisar (tarea 2.1/2.2):
        # DELETE /generations/{id} ---
        gen_to_delete = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Eliminar ({TAG})",
                    "kind": "knowledge",
                    "status": "ready",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_to_delete["id"])
        candidate_to_delete = (
            admin.table("exercise")
            .insert(
                {
                    "generation_id": gen_to_delete["id"],
                    "type": "knowledge",
                    "name": f"candidato a borrar {TAG}",
                    "statement": f"candidato a borrar {TAG}",
                    "code": [],
                    "expected_answer": "x",
                    "saved": False,
                }
            )
            .execute()
            .data[0]
        )
        created_exercise_ids.append(candidate_to_delete["id"])

        await generations.delete_generation(gen_to_delete["id"], _profile=tech_lead)
        pending_now = await generations.list_pending_generations(_profile=tech_lead)
        assert gen_to_delete["id"] not in {g.id for g in pending_now}, (
            "la generacion eliminada no debe aparecer en pendientes"
        )
        assert (
            admin.table("exercise").select("id").eq("id", candidate_to_delete["id"]).execute().data
            == []
        ), "los candidatos deben desaparecer en cascada con la generacion"
        assert (
            admin.table("generation").select("id").eq("id", gen_to_delete["id"]).execute().data
            == []
        ), "la fila de la generacion debe quedar borrada"
        print("OK: 2.1/2.2 eliminar una generacion ready la quita de pendientes y borra sus candidatos")

        gen_generating_delete = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"No borrar ({TAG})",
                    "kind": "knowledge",
                    "status": "generating",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_generating_delete["id"])
        try:
            await generations.delete_generation(gen_generating_delete["id"], _profile=tech_lead)
            raise AssertionError("eliminar una generacion generating deberia rechazarse")
        except HTTPException as exc:
            assert exc.status_code == 409
        print("OK: 2.1 eliminar una generacion generating se rechaza (409)")

        gen_ready_saved = (
            admin.table("generation")
            .insert(
                {
                    "repo_name": "",
                    "technologies": f"Con guardado ({TAG})",
                    "kind": "knowledge",
                    "status": "ready",
                    "created_by": tech_lead.id,
                }
            )
            .execute()
            .data[0]
        )
        created_generation_ids.append(gen_ready_saved["id"])
        saved_candidate = (
            admin.table("exercise")
            .insert(
                {
                    "generation_id": gen_ready_saved["id"],
                    "type": "knowledge",
                    "name": f"guardado {TAG}",
                    "statement": f"guardado {TAG}",
                    "code": [],
                    "expected_answer": "y",
                    "saved": True,
                }
            )
            .execute()
            .data[0]
        )
        created_exercise_ids.append(saved_candidate["id"])
        try:
            await generations.delete_generation(gen_ready_saved["id"], _profile=tech_lead)
            raise AssertionError("eliminar una generacion con ejercicios guardados deberia rechazarse")
        except HTTPException as exc:
            assert exc.status_code == 409
        assert (
            admin.table("generation").select("id").eq("id", gen_ready_saved["id"]).execute().data
        ), "la generacion con ejercicios guardados no debe borrarse"
        print("OK: 2.1 eliminar una generacion con ejercicios guardados se rechaza (409)")

        try:
            await generations.delete_generation(
                "00000000-0000-0000-0000-000000000000", _profile=tech_lead
            )
            raise AssertionError("eliminar una generacion inexistente deberia responder 404")
        except HTTPException as exc:
            assert exc.status_code == 404
        print("OK: 2.1 eliminar una generacion inexistente responde 404")

        # --- change catalogo-tecnologias (tareas 3.1/3.2): POST /generations
        # valida las tecnologias contra el catalogo ---
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[require_tech_lead] = lambda: tech_lead
        original_run_generation = generations.run_generation
        generations.run_generation = lambda *args, **kwargs: None  # no lanzar agentes
        try:
            client = TestClient(app)
            ok = client.post(
                "/generations",
                json={"technologies": ["Angular", "TypeScript"], "kind": "knowledge", "count": 1},
            )
            assert ok.status_code == 201, ok.text
            created_generation_ids.append(ok.json()["id"])

            variant = client.post(
                "/generations",
                json={"technologies": ["  angular  ", "TYPESCRIPT"], "kind": "knowledge", "count": 1},
            )
            assert variant.status_code == 201, variant.text
            created_generation_ids.append(variant.json()["id"])

            unknown_name = f"NoExiste-{TAG}"
            bad = client.post(
                "/generations",
                json={"technologies": ["Angular", unknown_name], "kind": "knowledge", "count": 1},
            )
            assert bad.status_code == 422, bad.text
            assert (
                admin.table("generation")
                .select("id")
                .like("technologies", f"%{unknown_name}%")
                .execute()
                .data
                == []
            ), "una tecnologia fuera del catalogo no debe crear ninguna generacion"
        finally:
            generations.run_generation = original_run_generation
            app.dependency_overrides.clear()

        for generation_id in (ok.json()["id"], variant.json()["id"]):
            stored = (
                admin.table("generation")
                .select("technologies")
                .eq("id", generation_id)
                .limit(1)
                .execute()
                .data[0]
            )
            assert stored["technologies"] == "Angular, TypeScript", stored["technologies"]
        print(
            "OK: 3.1/3.2 POST /generations canonicaliza las tecnologias del catalogo y "
            "rechaza (422) las que estan fuera sin crear generacion"
        )

        print("TODAS LAS COMPROBACIONES PASARON")
    finally:
        for exercise_id in created_exercise_ids:
            admin.table("exercise").delete().eq("id", exercise_id).execute()
        for generation_id in created_generation_ids:
            admin.table("generation").delete().eq("id", generation_id).execute()
        print("limpieza completada")


async def verify_full_flow(tech_lead: Profile) -> None:
    """Tarea 1.6: flujo completo contra agentes reales, generando sin
    repositorio (tipo `knowledge`, el unico que esta parte expone en el
    formulario -- design.md decision 5)."""
    admin = get_admin_client()

    gen_row = (
        admin.table("generation")
        .insert(
            {
                "repo_name": "",
                "technologies": f"Git ({TAG} full)",
                "kind": "knowledge",
                "status": "generating",
                "created_by": tech_lead.id,
            }
        )
        .execute()
        .data[0]
    )
    generation_id = gen_row["id"]

    try:
        print(f"generando (agentes reales)... generation_id={generation_id}")
        await orchestrator.run_generation(generation_id, ["Git"], None, None, "knowledge", 1, tech_lead.id)

        gen_after = (
            admin.table("generation")
            .select("status, error_message")
            .eq("id", generation_id)
            .limit(1)
            .execute()
            .data[0]
        )
        assert gen_after["status"] == "ready", (
            f"la generacion deberia quedar 'ready', llego '{gen_after['status']}' "
            f"({gen_after.get('error_message')})"
        )
        print("OK: 1.6 generar sin repositorio deja la generacion en 'ready'")

        pending = await generations.list_pending_generations(_profile=tech_lead)
        assert generation_id in {g.id for g in pending}
        print("OK: 1.6 la generacion 'ready' aparece en pendientes")

        detail = await generations.get_generation(generation_id, _profile=tech_lead)
        assert detail.status == "ready"
        assert len(detail.candidates) >= 1, "deberia haber al menos un candidato"
        candidate = detail.candidates[0]
        print(f"OK: 1.6 revisar la generacion devuelve {len(detail.candidates)} candidato(s)")

        saved = await exercises.save_exercise(
            candidate.id,
            body=SaveExerciseRequest(expected_answer=f"respuesta editada full {TAG}"),
            _tech_lead=tech_lead,
        )
        assert saved.expected_answer == f"respuesta editada full {TAG}"
        print("OK: 1.6 guardar un candidato con la respuesta esperada editada")

        closed = await generations.close_generation(generation_id, _profile=tech_lead)
        assert closed.status == "done"
        pending_after = await generations.list_pending_generations(_profile=tech_lead)
        assert generation_id not in {g.id for g in pending_after}
        print("OK: 1.6 cerrar la revision la quita de pendientes")

        # Sin filtro de texto: el enunciado lo genera el LLM de verdad y no
        # contiene TAG (que solo esta en el campo technologies, puesto a
        # mano al crear la generacion) -- a diferencia de los candidatos
        # fijos de la tarea 1.5, aqui no hay texto propio que buscar.
        listing_page = await exercises.list_saved_exercises(
            type=None, q=None, page=1, page_size=None, _tech_lead=tech_lead
        )
        saved_by_id = {e.id: e for e in listing_page.items}
        assert candidate.id in saved_by_id, "el ejercicio guardado deberia aparecer en GET /exercises"
        listed = saved_by_id[candidate.id]
        assert listed.technologies == [f"Git ({TAG} full)"], listed.technologies
        assert listed.repo is None
        print(
            f"OK: 1.6 el ejercicio guardado aparece en GET /exercises con "
            f"technologies={listed.technologies}"
        )

        print("TODAS LAS COMPROBACIONES DEL FLUJO COMPLETO PASARON")
    finally:
        admin.table("exercise").delete().eq("generation_id", generation_id).execute()
        admin.table("generation").delete().eq("id", generation_id).execute()
        print("limpieza del flujo completo terminada")


if __name__ == "__main__":
    asyncio.run(main())
    if "--full" in sys.argv[1:]:
        _tech_lead_rows = (
            get_admin_client()
            .table("profile")
            .select("id, email, name")
            .eq("role", "tech_lead")
            .limit(1)
            .execute()
            .data
        )
        _tech_lead = Profile(
            id=_tech_lead_rows[0]["id"],
            email=_tech_lead_rows[0]["email"],
            name=_tech_lead_rows[0]["name"],
            role="tech_lead",
        )
        asyncio.run(verify_full_flow(_tech_lead))
