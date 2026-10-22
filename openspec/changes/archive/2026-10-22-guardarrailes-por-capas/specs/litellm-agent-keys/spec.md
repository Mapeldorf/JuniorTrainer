# Spec Delta

## REMOVED Requirements

### Requirement: Exclusion del guardarrail global en la key del validador
**Reason**: El requisito existia unicamente para deshacer, en la virtual key del validador, un guardarrail de deteccion de inyeccion activado de forma global (`default_on: true`) que enmascaraba la PII antes de que el guardarrail de bloqueo pudiera verla. Este change elimina ese guardarrail global: la deteccion de inyeccion pasa a vincularse explicitamente a los deployments que la necesitan. Sin guardarrail global no hay nada de lo que excluirse, asi que el mecanismo de exclusion deja de tener objeto. La proteccion del validador no se reduce: su deteccion de inyeccion sigue en modo bloqueo sobre el deployment principal y el de respaldo (ver `technology-validation`), y el rechazo por dato personal se adelanta a la admision del agente (ver `pii-redaction`).

**Migration**: Hay que re-ejecutar `infra/litellm/provision_keys.py` tras desplegar la nueva configuracion del proxy. El script es idempotente y ya no aplica la metadata `opted_out_global_guardrails`, asi que las virtual keys existentes siguen siendo validas y no hay que regenerarlas ni redistribuirlas: la metadata que quede en una key existente es inerte, porque ya no hay ningun guardarrail global al que referirse. Se elimina tambien la verificacion manual `agents/validator/scripts/verify_guardrail_optout.py`, cuyo objeto desaparece con el requisito.
