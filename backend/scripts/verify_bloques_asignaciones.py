"""Verificacion manual end-to-end del change bloques-asignaciones (grupos
2-5): guardar/listar/eliminar ejercicios (exercise-catalog), crear/editar/
eliminar bloques (exercise-blocks) y asignar/progreso (block-assignment).

Llama directamente a las funciones de los routers (sin levantar un
servidor HTTP), contra el proyecto Supabase REAL configurado en el .env de
la raiz -- mismo patron que verify_generation_e2e.py. Crea sus propios
datos de prueba (una generacion + 3 ejercicios, marcados con un tag unico)
y los borra al terminar, incluso si una comprobacion falla.

Necesita que ya exista al menos un profile con role='tech_lead' y uno con
role='student' (los crea seed_tech_lead.py / POST /users).

Uso (desde backend/, con el venv del backend activo):
    python -m scripts.verify_bloques_asignaciones
"""

import asyncio
import uuid

from fastapi import HTTPException

from app.deps import require_tech_lead
from app.routers import blocks, exercises, users
from app.schemas.block import AssignBlockRequest, BlockCreateRequest, BlockUpdateRequest
from app.schemas.exercise import ExerciseDeleteRequest
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

TAG = f"verify-bloques-{uuid.uuid4().hex[:8]}"


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

    tech_lead_row = admin.table("profile").select("id, email, name, role").eq("role", "tech_lead").limit(1).execute().data
    student_row = admin.table("profile").select("id, email, name, role").eq("role", "student").limit(1).execute().data
    assert tech_lead_row, "no hay ningun profile con role='tech_lead' en este proyecto"
    assert student_row, "no hay ningun profile con role='student' en este proyecto"
    tech_lead = Profile(**tech_lead_row[0])
    student = Profile(**student_row[0])
    print(f"tech_lead: {tech_lead.email}  student: {student.email}")

    gen = admin.table("generation").insert(
        {"repo_name": TAG, "technologies": TAG, "kind": "knowledge", "status": "ready", "created_by": tech_lead.id}
    ).execute().data[0]
    ex1, ex2, ex3 = (
        row["id"]
        for row in admin.table("exercise")
        .insert(
            [
                {"generation_id": gen["id"], "type": "knowledge", "statement": f"{TAG} enunciado uno", "saved": False},
                {"generation_id": gen["id"], "type": "debug", "statement": f"{TAG} enunciado dos", "saved": False},
                {"generation_id": gen["id"], "type": "knowledge", "statement": f"{TAG} enunciado tres", "saved": False},
            ]
        )
        .execute()
        .data
    )

    block = None
    block2 = None
    try:
        # ---- exercise-catalog (2.2, 2.3, 2.4) ----
        saved1 = await exercises.save_exercise(ex1, body=None, _tech_lead=tech_lead)
        assert saved1.id == ex1
        print("OK: 2.2 guardar un candidato -> saved=true")

        await expect_http_error(
            exercises.save_exercise(ex1, body=None, _tech_lead=tech_lead), 409, "2.2 guardar dos veces falla"
        )

        await exercises.save_exercise(ex3, body=None, _tech_lead=tech_lead)

        listed = {e.id for e in await exercises.list_saved_exercises(type=None, q=None, _tech_lead=tech_lead)}
        assert ex1 in listed and ex3 in listed and ex2 not in listed
        print("OK: 2.3 GET /exercises solo devuelve definitivos (no eliminados, no candidatos)")

        # Comprobaciones por pertenencia, no por igualdad exacta de
        # conjuntos (bug preexistente arreglado aqui): el entorno real
        # puede tener otros ejercicios guardados ajenos a esta prueba, y
        # la igualdad exacta falla en cuanto hay alguno de tipo
        # "knowledge" fuera del tag de esta ejecucion.
        listed_knowledge = {
            e.id for e in await exercises.list_saved_exercises(type="knowledge", q=None, _tech_lead=tech_lead)
        }
        assert ex1 in listed_knowledge and ex3 in listed_knowledge and ex2 not in listed_knowledge
        print("OK: 2.3 filtro por type")

        listed_q = {
            e.id for e in await exercises.list_saved_exercises(type=None, q="enunciado uno", _tech_lead=tech_lead)
        }
        assert ex1 in listed_q and ex2 not in listed_q and ex3 not in listed_q
        print("OK: 2.3 filtro por texto (q)")

        deleted = await exercises.delete_exercise(ex3, ExerciseDeleteRequest(deleted=True), tech_lead)
        assert deleted.id == ex3  # SavedExercise no expone deleted_at; solo confirma que no lanzo error
        listed_after = {e.id for e in await exercises.list_saved_exercises(type=None, q=None, _tech_lead=tech_lead)}
        assert ex3 not in listed_after
        print("OK: 2.4 borrado logico: deja de aparecer en GET /exercises")

        # ---- exercise-blocks (3.2-3.5) ----
        await expect_http_error(
            blocks.create_block(BlockCreateRequest(name=f"{TAG} invalido", exercise_ids=[ex3]), tech_lead),
            400,
            "3.2 crear bloque con un ejercicio eliminado falla",
        )

        block = await blocks.create_block(BlockCreateRequest(name=f"{TAG} bloque", exercise_ids=[ex1]), tech_lead)
        assert len(block.exercises) == 1 and block.exercises[0].exercise.id == ex1
        assert block.resolved is False and block.exercises[0].exercise_deleted is False
        print("OK: 3.2 crear bloque con un ejercicio definitivo")

        listing = await blocks.list_blocks(deleted=False, _tech_lead=tech_lead)
        listed_block = next(b for b in listing if b.id == block.id)
        assert listed_block.resolved is False and listed_block.assigned_students == []
        detail = await blocks.get_block(block.id, tech_lead)
        assert detail.id == block.id and detail.resolved is False
        print("OK: 3.3 GET /blocks y GET /blocks/{id}; sin asignaciones -> resolved=false, assigned_students=[]")

        usage_before = {
            e.id: e.block_usage_count
            for e in await exercises.list_saved_exercises(type=None, q=None, _tech_lead=tech_lead)
        }
        assert usage_before[ex1] == 1
        print("OK: 2.2 block_usage_count refleja el bloque recien creado")

        updated = await blocks.update_block(block.id, BlockUpdateRequest(name=f"{TAG} editado"), tech_lead)
        assert updated.name == f"{TAG} editado"
        print("OK: 3.4 editar nombre de un bloque sin respuestas")

        # ---- block-assignment (4.2-4.4) ----
        assign1 = await blocks.assign_block(block.id, AssignBlockRequest(student_ids=[student.id]), tech_lead)
        assert assign1.results[0].status == "created"
        assign2 = await blocks.assign_block(block.id, AssignBlockRequest(student_ids=[student.id]), tech_lead)
        assert assign2.results[0].status == "already_assigned"
        print("OK: 4.2 asignar bloque a alumno; reasignar al mismo se omite sin error")

        listing_assigned = await blocks.list_blocks(deleted=False, _tech_lead=tech_lead)
        listed_assigned = next(b for b in listing_assigned if b.id == block.id)
        assert listed_assigned.resolved is False
        assert {s.id for s in listed_assigned.assigned_students} == {student.id}
        print("OK: 1.2 GET /blocks muestra al alumno en assigned_students, resolved sigue false")

        # ---- block-assignment (1.2 frontend-tech-lead-alumnos): segundo
        # bloque para el mismo alumno, usado mas abajo para comprobar
        # GET /users/{id}/blocks a traves de varios bloques.
        block2 = await blocks.create_block(BlockCreateRequest(name=f"{TAG} bloque 2", exercise_ids=[ex1]), tech_lead)
        await blocks.assign_block(block2.id, AssignBlockRequest(student_ids=[student.id]), tech_lead)
        print("OK: 4.2 segundo bloque creado y asignado al mismo alumno")

        progress = await blocks.get_block_progress(block.id, tech_lead)
        assert len(progress) == 1 and progress[0].exercises[0].answered is False
        assert progress[0].exercises[0].type == "knowledge"
        assert progress[0].exercises[0].statement == f"{TAG} enunciado uno"
        assert progress[0].exercises[0].answer_text is None and progress[0].exercises[0].justification is None
        print("OK: 4.3 progreso sin respuestas todavia; incluye type/statement de la copia")

        assignment_id = progress[0].assignment_id
        admin.table("answer").insert(
            {
                "assignment_id": assignment_id,
                "exercise_id": ex1,
                "text": "respuesta de prueba",
                "verdict": "correct",
                "justification": "justificacion de prueba",
            }
        ).execute()

        progress_after = await blocks.get_block_progress(block.id, tech_lead)
        assert progress_after[0].exercises[0].answered is True
        assert progress_after[0].exercises[0].answer_text == "respuesta de prueba"
        assert progress_after[0].exercises[0].justification == "justificacion de prueba"
        print("OK: 4.3 progreso refleja la respuesta insertada, con texto y justificacion")

        listing_resolved = await blocks.list_blocks(deleted=False, _tech_lead=tech_lead)
        listed_resolved = next(b for b in listing_resolved if b.id == block.id)
        assert listed_resolved.resolved is True
        detail_resolved = await blocks.get_block(block.id, tech_lead)
        assert detail_resolved.resolved is True
        print("OK: 1.2/1.3 con una respuesta registrada, GET /blocks y GET /blocks/{id} marcan resolved=true")

        await expect_http_error(
            blocks.update_block(block.id, BlockUpdateRequest(name=f"{TAG} no deberia aplicarse"), tech_lead),
            409,
            "3.4 editar un bloque ya resuelto falla (trigger 0005)",
        )

        await exercises.delete_exercise(ex1, ExerciseDeleteRequest(deleted=True), tech_lead)
        progress_still = await blocks.get_block_progress(block.id, tech_lead)
        assert progress_still[0].exercises[0].exercise_id == ex1 and progress_still[0].exercises[0].answered is True
        print("OK: 4.4 eliminar el ejercicio despues de asignar no cambia la copia")

        detail_with_deleted_exercise = await blocks.get_block(block.id, tech_lead)
        assert detail_with_deleted_exercise.exercises[0].exercise_deleted is True
        print("OK: 1.3 GET /blocks/{id} marca exercise_deleted=true para el ejercicio eliminado del catalogo")

        deleted_block = await blocks.delete_block(block.id, tech_lead)
        assert deleted_block.deleted_at is not None
        print("OK: 3.5 borrado logico del bloque")

        await expect_http_error(
            blocks.assign_block(block.id, AssignBlockRequest(student_ids=[student.id]), tech_lead),
            409,
            "4.2 asignar un bloque eliminado falla",
        )

        progress_final = await blocks.get_block_progress(block.id, tech_lead)
        assert progress_final[0].exercises[0].answered is True
        listing_deleted = await blocks.list_blocks(deleted=True, _tech_lead=tech_lead)
        assert block.id in {b.id for b in listing_deleted}
        print("OK: 4.4/3.5 eliminar el bloque no cambia la copia ya asignada; aparece en 'Bloques eliminados'")

        # ---- block-assignment (1.2 frontend-tech-lead-alumnos): "Consultar
        # las asignaciones de un alumno a traves de sus bloques" ----
        # Comprobaciones por pertenencia, no por igualdad exacta (mismo
        # ajuste que en 2.3): el entorno real puede tener otras
        # asignaciones de este alumno ajenas a esta prueba.
        student_blocks = await users.get_student_blocks(student.id, _tech_lead=tech_lead)
        by_block_id = {sba.block_id: sba for sba in student_blocks}
        assert block.id in by_block_id and block2.id in by_block_id, (
            "se esperaban ambas asignaciones de prueba en GET /users/{id}/blocks"
        )
        our_blocks_order = [sba.block_id for sba in student_blocks if sba.block_id in (block.id, block2.id)]
        assert our_blocks_order == [block.id, block2.id], (
            "se esperaba el orden de asignacion (block1 antes que block2)"
        )
        assert by_block_id[block.id].block_name == f"{TAG} editado"
        assert by_block_id[block.id].exercises[0].answered is True
        assert by_block_id[block.id].exercises[0].answer_text == "respuesta de prueba"
        assert by_block_id[block2.id].block_name == f"{TAG} bloque 2"
        assert by_block_id[block2.id].exercises[0].answered is False
        print("OK: GET /users/{id}/blocks incluye ambos bloques (incluido el ya eliminado), con su block_name y detalle por ejercicio")

        # get_student_blocks() en si no comprueba el rol -- lo hace la
        # propia dependencia require_tech_lead, asi que se prueba esa
        # dependencia directamente con el Profile del alumno (mismo patron
        # que verify_valoracion_respuestas.py).
        await expect_http_error(
            require_tech_lead(profile=student),
            403,
            "GET /users/{id}/blocks: un alumno no puede llamarlo (require_tech_lead rechaza su Profile)",
        )

        await expect_http_error(
            users.get_student_blocks(tech_lead.id, _tech_lead=tech_lead), 404, "GET /users/{id}/blocks con un id que no es alumno"
        )

        print("\nTODAS LAS COMPROBACIONES PASARON")

    finally:
        for b in (block, block2):
            if b is None:
                continue
            assignment_ids = [
                row["id"]
                for row in admin.table("assignment").select("id").eq("block_id", b.id).execute().data or []
            ]
            if assignment_ids:
                admin.table("answer").delete().in_("assignment_id", assignment_ids).execute()
                admin.table("assignment_exercise").delete().in_("assignment_id", assignment_ids).execute()
                admin.table("assignment").delete().in_("id", assignment_ids).execute()
            admin.table("block_exercise").delete().eq("block_id", b.id).execute()
            admin.table("block").delete().eq("id", b.id).execute()
        admin.table("exercise").delete().in_("id", [ex1, ex2, ex3]).execute()
        admin.table("generation").delete().eq("id", gen["id"]).execute()
        print("limpieza de datos de prueba completada")


if __name__ == "__main__":
    asyncio.run(main())
