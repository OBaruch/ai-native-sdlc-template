# Cómo adoptar la plantilla

[Guía completa en inglés](adoption.md) · [Contrato para cualquier agente](../.agents/README.md)

**Para un proyecto nuevo, usa “Use this template → Create a new repository” en GitHub.**
Obtienes un repositorio independiente, con tu propio historial y configuración. Un **fork**
conviene para contribuir a esta plantilla o mantener una relación con el proyecto original.
Un **clone** solo crea una copia local. Si el botón de plantilla no aparece, el propietario
puede activarlo en Settings → General → Template repository; puedes usar un fork como alternativa.

Desde GitHub CLI, si está habilitada la opción de plantilla:

```bash
gh repo create TU_USUARIO/TU_PROYECTO --template OBaruch/ai-native-sdlc-template --private --clone
cd TU_PROYECTO
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install 'PyYAML==6.0.3'
make doctor
make template-check
```

También necesitas Bash, Git, Make y ShellCheck. Instala ShellCheck con el gestor de paquetes
de tu sistema. Estas verificaciones no llaman a ningún modelo ni requieren una API key.
Las credenciales, variables, protecciones de ramas y entornos de producción **no se copian**:
configúralos en tu propio repositorio. Para integrar la plantilla en un proyecto existente,
hazlo en una rama y conserva sus instrucciones, código, historial y CI.

## Instrucciones que puedes darle a tu agente

> Lee AGENTS.md, .agents/README.md y docs/adoption.md. Inspecciona mi proyecto y adapta la
> plantilla en una rama, conservando los archivos existentes y las credenciales. Usa AGENTS.md
> y .agents como fuente única de instrucciones y políticas. Elige explícitamente el harness,
> verifica sus permisos reales y configura los comandos Make, responsables y aprobaciones.
> Ejecuta doctor, template-check y las pruebas del proyecto. Distingue pruebas aprobadas,
> fallidas, deshabilitadas y no ejecutadas. Abre un PR para revisión humana; no lo apruebes,
> fusiones ni despliegues por tu cuenta.

Codex lee AGENTS.md; Claude Code conserva sus archivos de descubrimiento mediante un adaptador
generado. Otros agentes pueden leer los mismos Markdown o recibirlos como contexto explícito.
No necesitan soportar slash commands ni subagentes para usar las instrucciones y políticas.

Para ejecutar un agente, selecciona `SDLC_AGENT_ADAPTER=codex` o `claude`, instala una versión
exacta y configura su autenticación segura. Para Hermes, Muse, Dots, Grok u otro harness,
usa `SDLC_AGENT_ADAPTER=command` e implementa el contrato JSON documentado. Declarar permisos
no los impone: verifica el sandbox real antes de habilitar tareas con escritura.

Antes de activar `SDLC_ENABLED=true`, configura los comandos de tu aplicación, las políticas,
los responsables, evals reales, protecciones de ramas y aprobaciones de producción. La guía
completa incluye las variables de GitHub, la migración y los límites de cada adaptador.
