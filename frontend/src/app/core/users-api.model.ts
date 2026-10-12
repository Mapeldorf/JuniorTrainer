/**
 * DTOs de `GET /users` (capacidad `user-auth`, ya implementada; cliente
 * nuevo en la tarea 8.3 de frontend-tech-lead-bloques, para la seccion
 * "Asignar a mas alumnos" de la pantalla 7 -- ver design.md). Se replica
 * a mano, igual que el resto de `*-api.model.ts`.
 */
export interface StudentSummary {
  id: string;
  name: string;
  email: string;
}
