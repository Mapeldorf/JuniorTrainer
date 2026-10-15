# Spec Delta

## MODIFIED Requirements

### Requirement: Content-Security-Policy estricta sin inline
El sistema SHALL incluir en toda respuesta HTML servida por el frontend una cabecera `Content-Security-Policy` cuyo `default-src` sea `'self'`, que no incluya `'unsafe-inline'` ni `'unsafe-eval'` en ningun directive, y que solo permita como origenes externos los que la aplicacion necesita realmente para funcionar (la URL de la API/Supabase configuradas en el build). La aplicacion no carga fuentes web, por lo que la politica SHALL NOT permitir origenes de fuentes externas como `fonts.googleapis.com` ni `fonts.gstatic.com`.

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita `GET /` o cualquier ruta que resuelva a `index.html`
- **THEN** la respuesta incluye una `Content-Security-Policy` con `default-src 'self'`
- **AND** ningun directive de esa politica incluye `'unsafe-inline'` ni `'unsafe-eval'`

#### Scenario: El bundle de produccion no depende de contenido inline
- **WHEN** se genera el build de produccion del frontend
- **THEN** el `index.html` resultante no contiene ningun `<script>`, `<style>` ni atributo `style=""` inline
- **AND** la aplicacion sigue funcionando correctamente bajo la Content-Security-Policy sin `'unsafe-inline'`

#### Scenario: Sin origenes de fuentes externas
- **WHEN** se inspecciona la `Content-Security-Policy` servida por el frontend
- **THEN** ni `style-src` ni `font-src` incluyen `fonts.googleapis.com` ni `fonts.gstatic.com`
