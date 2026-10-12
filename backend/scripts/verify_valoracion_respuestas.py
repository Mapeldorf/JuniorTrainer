"""Verificacion manual end-to-end de valoracion-respuestas y de su
ajuste posterior en frontend-alumno (tarea 1.4): listar/ver asignaciones
propias (student-assignments), responder un ejercicio y que la respuesta
quede evaluada y persistida (answer-evaluation), progreso con verdict
(block-assignment modificada), listar alumnos (user-auth modificada), y
-- lo que anade frontend-alumno -- que `GET /assignments` informe
`answered_count`/`total_count` y que `GET /assignments/{id}` corte en el
primer ejercicio sin responder exponiendo el texto/verdict/justificacion
de los ya respondidos (student-assignments modificada otra vez).

Llama directamente a las funciones de los routers (sin levantar un
servidor HTTP), contra el proyecto Supabase REAL configurado en el .env de
la raiz y contra los agentes evaluador/revisor REALES -- mismo patron que
verify_bloques_asignaciones.py y verify_generation_e2e.py. Crea sus
propios datos de prueba (una generacion + 3 ejercicios + un bloque,
marcados con un tag unico, mas un segundo alumno desechable para probar
"asignacion de otro alumno") y los borra al terminar, incluso si una
comprobacion falla.

Necesita que ya exista al menos un profile con role='tech_lead' y uno con
role='student' (los crea seed_tech_lead.py / POST /users).

Preparacion (dos terminales, cada uno con su propio venv y su .env real).
IMPORTANTE: `AGENT_EVALUATOR_URL`/`AGENT_REVIEWER_URL` hay que fijarlas
TAMBIEN al arrancar cada agente, no solo al correr este script -- el
cliente A2A (`create_client`) resuelve primero la Agent Card en la URL que
se le pasa y LUEGO envia el mensaje real a la URL que esa tarjeta declara
(`AgentInterface.url`, construida en `app/agent_card.py` a partir de
`settings.agent_evaluator_url`/`agent_reviewer_url`). Si el agente arranca
sin esa variable, su propia tarjeta sigue anunciando el nombre de servicio
de docker-compose (`http://agent-evaluator:8013/`), que no resuelve por
DNS fuera de la red de Compose -- de ahi un `getaddrinfo failed` aunque la
URL que le pasamos a este script sea `127.0.0.1` (confirmado en vivo: el
mensaje de error solo muestra la URL de descubrimiento, no la que el SDK
usa de verdad para el envio).

  1. agents/evaluator (venv propio):
       set AGENT_EVALUATOR_URL=http://127.0.0.1:8013/   (o $env:AGENT_EVALUATOR_URL=... en PowerShell)
       set LITELLM_BASE_URL=http://127.0.0.1:4000/v1    (mismo problema: el default
                                                          `http://litellm:4000/v1` tampoco
                                                          resuelve fuera de la red de Compose;
                                                          necesita `docker compose up -d litellm`
                                                          con su puerto publicado al host)
       uvicorn app.main:app --host 0.0.0.0 --port 8013
  2. agents/reviewer (venv propio):
       set AGENT_REVIEWER_URL=http://127.0.0.1:8014/
       set LITELLM_BASE_URL=http://127.0.0.1:4000/v1
       uvicorn app.main:app --host 0.0.0.0 --port 8014

Uso (desde backend/, con el venv del backend activo):
    AGENT_EVALUATOR_URL=http://127.0.0.1:8013/ AGENT_REVIEWER_URL=http://127.0.0.1:8014/ \
    python -m scripts.verify_valoracion_respuestas

(Los valores por defecto de AGENT_EVALUATOR_URL/AGENT_REVIEWER_URL son los
nombres de servicio de docker-compose; sobreescribirlos a localhost para
esta verificacion suelta, igual que en verify_generation_e2e.py -- pero
en los TRES sitios: los dos agentes y este script.)
"""

import asyncio
import uuid

from fastapi import HTTPException

import app.tracing as tracing
from app.deps import require_tech_lead
from app.routers import assignments, blocks, exercises, users
from app.schemas.assignment import AnswerRequest
from app.schemas.block import AssignBlockRequest, BlockCreateRequest
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

TAG = f"verify-valoracion-{uuid.uuid4().hex[:8]}"

# Para las tareas 3.3/4.3/5.6 ("verificar que el trace_id aparece en la
# traza registrada en Langfuse"): capturamos el primer trace_id real que
# genera `answer_exercise` (mismo patron que verify_generation_e2e.py --
# `assignments.py` importa `new_trace_id` por nombre, asi que hay que
# parchear la referencia que usa ese modulo, no solo `app.tracing`).
_original_new_trace_id = tracing.new_trace_id
_captured: dict = {}


def _capturing_new_trace_id() -> str:
    trace_id = _original_new_trace_id()
    _captured.setdefault("trace_id", trace_id)
    return trace_id


assignments.new_trace_id = _capturing_new_trace_id


async def expect_http_error(coro, status_code: int, label: str) -> None:
    try:
        await coro
    except HTTPException as exc:
        assert exc.status_code == status_code, f"{label}: se esperaba {status_code}, llego {exc.status_code}"
        print(f"OK: {label} (HTTP {exc.status_code})")
        return
    raise AssertionError(f"{label}: no lanzo HTTPException")


async def main() -> None:
    admin = get_admin_client()

    tech_lead_row = (
        admin.table("profile").select("id, email, name, role").eq("role", "tech_lead").limit(1).execute().data
    )
    student_row = (
        admin.table("profile").select("id, email, name, role").eq("role", "student").limit(1).execute().data
    )
    assert tech_lead_row, "no hay ningun profile con role='tech_lead' en este proyecto"
    assert student_row, "no hay ningun profile con role='student' en este proyecto"
    tech_lead = Profile(**tech_lead_row[0])
    student_a = Profile(**student_row[0])
    print(f"tech_lead: {tech_lead.email}  student_a: {student_a.email}")

    # Segundo alumno desechable (solo para el escenario "asignacion de
    # otro alumno"): se crea aqui mismo con la Admin API (igual que
    # scripts/seed_tech_lead.py) y se borra al terminar.
    student_b_email = f"{TAG}@example.com"
    created_user = admin.auth.admin.create_user(
        {
            "email": student_b_email,
            "password": uuid.uuid4().hex,
            "email_confirm": True,
            "user_metadata": {"name": f"{TAG} alumno B", "role": "student"},
        }
    )
    assert created_user.user is not None, "no se ha podido crear el segundo alumno de prueba"
    student_b_id = created_user.user.id
    student_b_row = admin.table("profile").select("id, email, name, role").eq("id", student_b_id).limit(1).execute().data
    assert student_b_row, "el trigger on_auth_user_created no ha creado el Profile del segundo alumno"
    student_b = Profile(**student_b_row[0])
    print(f"student_b (desechable): {student_b.email}")

    gen = (
        admin.table("generation")
        .insert({"repo_name": TAG, "technologies": TAG, "kind": "knowledge", "status": "ready", "created_by": tech_lead.id})
        .execute()
        .data[0]
    )
    ex_correct, ex_wrong, ex_outside, ex_deleted = (
        row["id"]
        for row in admin.table("exercise")
        .insert(
            [
                {
                    "generation_id": gen["id"],
                    "type": "knowledge",
                    "statement": f"{TAG}: cuanto es 2+2?",
                    "expected_answer": "4",
                    "saved": False,
                },
                {
                    "generation_id": gen["id"],
                    "type": "knowledge",
                    "statement": f"{TAG}: cuanto es 3+3?",
                    "expected_answer": "6",
                    "saved": False,
                },
                {
                    "generation_id": gen["id"],
                    "type": "knowledge",
                    "statement": f"{TAG}: ejercicio fuera de la asignacion",
                    "expected_answer": "da igual",
                    "saved": False,
                },
                {
                    "generation_id": gen["id"],
                    "type": "knowledge",
                    "statement": f"{TAG}: cuanto es 5+5? (se elimina tras asignar)",
                    "expected_answer": "10",
                    "saved": False,
                },
            ]
        )
        .execute()
        .data
    )

    block = None
    try:
        # body=None (bug preexistente arreglado aqui: estas llamadas
        # pasaban tech_lead como segundo posicional -- el parametro body --
        # desde que bloques-asignaciones le anadio ese parametro a
        # save_exercise(); ahora va como _tech_lead=, igual que el resto
        # de llamadas en este archivo).
        await exercises.save_exercise(ex_correct, body=None, _tech_lead=tech_lead)
        await exercises.save_exercise(ex_wrong, body=None, _tech_lead=tech_lead)
        await exercises.save_exercise(ex_outside, body=None, _tech_lead=tech_lead)
        await exercises.save_exercise(ex_deleted, body=None, _tech_lead=tech_lead)

        # Bloque con 3 de los 4 ejercicios: ex_outside se queda fuera a
        # proposito, para el escenario "responder un ejercicio que no esta
        # en la propia asignacion"; ex_deleted entra en el bloque pero se
        # eliminara (deleted_at) DESPUES de asignar, para el escenario "el
        # ejercicio original fue eliminado tras asignar el bloque".
        block = await blocks.create_block(
            BlockCreateRequest(name=f"{TAG} bloque", exercise_ids=[ex_correct, ex_wrong, ex_deleted]), tech_lead
        )
        print("OK: bloque de prueba creado con 3 ejercicios")

        assign_result = await blocks.assign_block(
            block.id, AssignBlockRequest(student_ids=[student_a.id, student_b.id]), tech_lead
        )
        assert all(r.status == "created" for r in assign_result.results)
        print("OK: bloque asignado a los dos alumnos de prueba")

        # ---- student-assignments (tareas 2.2/2.3) ----
        # Busqueda por pertenencia, no por indice/longitud exacta (mismo
        # ajuste que en verify_bloques_asignaciones.py): student_a es el
        # alumno real de pruebas manuales, que puede tener otras
        # asignaciones ajenas a esta ejecucion.
        listing_a = await assignments.list_my_assignments(student=student_a)
        asignacion_a = next(a for a in listing_a if a.block_name == f"{TAG} bloque")
        assignment_a_id = asignacion_a.id
        print("OK: 2.2 GET /assignments devuelve la asignacion propia (entre posiblemente otras)")

        listing_b = await assignments.list_my_assignments(student=student_b)
        assert len(listing_b) == 1
        assignment_b_id = listing_b[0].id
        print("OK: 2.2 GET /assignments del segundo alumno devuelve la suya (distinta)")

        detail_a = await assignments.get_my_assignment_detail(assignment_a_id, student=student_a)
        # frontend-alumno 1.3: con 0 de 3 respondidos, el detalle corta en el
        # primer ejercicio sin responder (inclusive) -- con nada respondido
        # todavia, eso es solo el primero por posicion (ex_correct), nunca
        # ex_wrong ni ex_deleted.
        assert {e.exercise_id for e in detail_a.exercises} == {ex_correct}, (
            f"con 0 de 3 respondidos, el detalle debe devolver solo el primero por posicion (ex_correct); "
            f"llego {[e.exercise_id for e in detail_a.exercises]!r}"
        )
        assert all(not e.answered for e in detail_a.exercises)
        print("OK: 2.3 GET /assignments/{id} corta en el primer ejercicio (sin responder todavia)")

        listing_a_sin_respuestas = await assignments.list_my_assignments(student=student_a)
        progreso_a = next(a for a in listing_a_sin_respuestas if a.id == assignment_a_id)
        assert progreso_a.answered_count == 0 and progreso_a.total_count == 3
        print("OK: frontend-alumno 1.2 GET /assignments informa 0/3 antes de responder nada")

        await expect_http_error(
            assignments.get_my_assignment_detail(assignment_b_id, student=student_a),
            404,
            "2.3 ver el detalle de la asignacion de otro alumno",
        )

        # ---- answer-evaluation (tareas 5.4/5.5) ----
        result_correct = await assignments.answer_exercise(
            assignment_a_id, ex_correct, AnswerRequest(text="4"), student=student_a
        )
        assert result_correct.verdict == "correct", f"se esperaba verdict=correct, llego {result_correct.verdict!r}"
        assert result_correct.justification
        print(f"OK: 5.4 respuesta correcta evaluada -> verdict={result_correct.verdict!r}")

        detail_a_parcial = await assignments.get_my_assignment_detail(assignment_a_id, student=student_a)
        assert {e.exercise_id for e in detail_a_parcial.exercises} == {ex_correct, ex_wrong}, (
            "con 1 de 3 respondidos, el detalle para el alumno debe cortar en el siguiente sin "
            f"responder (ex_wrong) y nunca llegar a ex_deleted; llego {[e.exercise_id for e in detail_a_parcial.exercises]!r}"
        )
        ex_correct_item = next(e for e in detail_a_parcial.exercises if e.exercise_id == ex_correct)
        assert ex_correct_item.answered and ex_correct_item.answer_text == "4"
        assert ex_correct_item.verdict == "correct" and ex_correct_item.justification
        ex_wrong_item = next(e for e in detail_a_parcial.exercises if e.exercise_id == ex_wrong)
        assert not ex_wrong_item.answered and ex_wrong_item.answer_text is None and ex_wrong_item.verdict is None
        print(
            "OK: frontend-alumno 1.3 GET /assignments/{id} corta en el siguiente sin responder "
            "(no incluye ex_deleted) y expone texto/verdict/justificacion del ya respondido"
        )

        listing_a_parcial = await assignments.list_my_assignments(student=student_a)
        progreso_a_parcial = next(a for a in listing_a_parcial if a.id == assignment_a_id)
        assert progreso_a_parcial.answered_count == 1 and progreso_a_parcial.total_count == 3
        print("OK: frontend-alumno 1.2 GET /assignments informa 1/3 tras responder un ejercicio")

        result_wrong = await assignments.answer_exercise(
            assignment_a_id, ex_wrong, AnswerRequest(text="una tortuga"), student=student_a
        )
        assert result_wrong.verdict in ("incomplete", "incorrect"), f"verdict inesperado: {result_wrong.verdict!r}"
        print(f"OK: 5.4 respuesta incorrecta evaluada -> verdict={result_wrong.verdict!r}")

        await expect_http_error(
            assignments.answer_exercise(assignment_a_id, ex_correct, AnswerRequest(text="4 otra vez"), student=student_a),
            409,
            "5.5 responder dos veces el mismo ejercicio",
        )

        unchanged = (
            admin.table("answer")
            .select("text")
            .eq("assignment_id", assignment_a_id)
            .eq("exercise_id", ex_correct)
            .limit(1)
            .execute()
            .data[0]
        )
        assert unchanged["text"] == "4", "la respuesta doble no debe modificar la original (trigger reject_update)"
        print("OK: 5.5 la respuesta original no cambia tras el intento de doble respuesta")

        await expect_http_error(
            assignments.answer_exercise(assignment_a_id, ex_outside, AnswerRequest(text="lo que sea"), student=student_a),
            404,
            "responder un ejercicio que no esta en la propia asignacion",
        )

        await expect_http_error(
            assignments.answer_exercise(assignment_b_id, ex_correct, AnswerRequest(text="4"), student=student_a),
            404,
            "responder usando el assignment_id de otro alumno",
        )

        # ---- La evaluacion usa la copia, nunca el exercise original
        # (requisito de answer-evaluation: "el ejercicio original fue
        # eliminado tras asignar el bloque") ----
        from app.schemas.exercise import ExerciseDeleteRequest

        await exercises.delete_exercise(ex_deleted, ExerciseDeleteRequest(deleted=True), tech_lead)
        result_after_delete = await assignments.answer_exercise(
            assignment_a_id, ex_deleted, AnswerRequest(text="10"), student=student_a
        )
        assert result_after_delete.verdict == "correct", (
            f"se esperaba verdict=correct usando la copia (expected_answer='10'), llego {result_after_delete.verdict!r}"
        )
        print("OK: responder un ejercicio cuyo exercise original ya tiene deleted_at usa igual la copia de la asignacion")

        # ---- block-assignment modificada (tarea 6.1) ----
        listing_a_completa = await assignments.list_my_assignments(student=student_a)
        progreso_a_completo = next(a for a in listing_a_completa if a.id == assignment_a_id)
        assert progreso_a_completo.answered_count == 3 and progreso_a_completo.total_count == 3
        print("OK: frontend-alumno 1.2 GET /assignments informa 3/3 con la asignacion completada")

        detail_a_completo = await assignments.get_my_assignment_detail(assignment_a_id, student=student_a)
        assert {e.exercise_id for e in detail_a_completo.exercises} == {ex_correct, ex_wrong, ex_deleted}
        assert all(e.answered and e.verdict is not None and e.answer_text is not None for e in detail_a_completo.exercises)
        print("OK: frontend-alumno 1.3 GET /assignments/{id} de una asignacion completada expone los 3 con su valoracion")

        progress = await blocks.get_block_progress(block.id, tech_lead)
        progress_a = next(p for p in progress if p.student_id == student_a.id)
        verdict_by_exercise = {e.exercise_id: e.verdict for e in progress_a.exercises}
        assert verdict_by_exercise[ex_correct] == "correct"
        assert verdict_by_exercise[ex_wrong] == result_wrong.verdict
        assert verdict_by_exercise[ex_deleted] == "correct"
        progress_b = next(p for p in progress if p.student_id == student_b.id)
        assert all(e.verdict is None and not e.answered for e in progress_b.exercises)
        print("OK: 6.1 el progreso del bloque muestra el verdict real de cada respuesta evaluada")

        # ---- user-auth modificada (tarea 7.1) ----
        student_list = await users.list_students(_tech_lead=tech_lead)
        student_ids = {s.id for s in student_list}
        assert student_a.id in student_ids and student_b.id in student_ids
        print("OK: 7.1 GET /users (tech lead) incluye a los alumnos de prueba")

        # list_students() en si no comprueba el rol -- lo hace la propia
        # dependencia require_tech_lead (ya cubierta por la tarea 1.1), asi
        # que aqui se prueba esa dependencia directamente con el Profile
        # del alumno, igual que en tasks.md tarea 1.1.
        await expect_http_error(
            require_tech_lead(profile=student_a),
            403,
            "7.1 un alumno no puede listar alumnos (require_tech_lead rechaza su Profile)",
        )

        trace_id = _captured.get("trace_id")
        if trace_id:
            from langfuse import get_client

            tracing.init_client()
            print()
            print(f"trace_id: {trace_id}")
            print(f"URL: {get_client().get_trace_url(trace_id=trace_id)}")
            print(
                "OK: revisa esa traza en Langfuse Cloud (puede tardar unos segundos en aparecer, "
                "tareas 3.3/4.3/5.6) y comprueba que 'orquestacion-respuesta' (backend), "
                "'agente-evaluador' y 'agente-revisor' aparecen bajo el mismo trace_id"
            )

        print("\nTODAS LAS COMPROBACIONES PASARON")

    finally:
        if block is not None:
            assignment_ids = [
                row["id"]
                for row in admin.table("assignment").select("id").eq("block_id", block.id).execute().data or []
            ]
            if assignment_ids:
                admin.table("answer").delete().in_("assignment_id", assignment_ids).execute()
                admin.table("assignment_exercise").delete().in_("assignment_id", assignment_ids).execute()
                admin.table("assignment").delete().in_("id", assignment_ids).execute()
            admin.table("block_exercise").delete().eq("block_id", block.id).execute()
            admin.table("block").delete().eq("id", block.id).execute()
        admin.table("exercise").delete().in_("id", [ex_correct, ex_wrong, ex_outside, ex_deleted]).execute()
        admin.table("generation").delete().eq("id", gen["id"]).execute()
        admin.auth.admin.delete_user(student_b_id)
        print("limpieza de datos de prueba completada (incluido el segundo alumno desechable)")


if __name__ == "__main__":
    asyncio.run(main())
