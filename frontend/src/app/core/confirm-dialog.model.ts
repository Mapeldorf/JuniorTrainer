/**
 * Peticion de confirmacion (change `dialogo-confirmacion-tailwind`,
 * capacidad `confirm-dialog`): cada punto de la app que necesita
 * confirmar/cancelar una accion indica su propio titulo, mensaje y texto
 * de los botones (requisito "Textos configurables por cada uso").
 * `destructive` colorea el boton de confirmar en rojo cuando la accion
 * protegida borra algo.
 */
export interface ConfirmDialogRequest {
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  destructive?: boolean;
}

export type ConfirmDialogOptions = ConfirmDialogRequest;
