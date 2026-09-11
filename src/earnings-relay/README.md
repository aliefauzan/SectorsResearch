# Earnings Relay — src/earnings-relay/

Referencia: los archivos de trabajo viven en este directorio y en los worktrees
`agent-a4f7a77654cae400b` y `agent-a240b5e99b23b9b8e` (dentro de `.claude/worktrees/`).

## Comando para correr

```bash
python3 run.sh
```

Esto inicia el mock API (`mock_server.py`) y luego el UI (`webapp.py`).

## Comando para probar

```bash
python3 attack_classes.py --run
```

Ejecuta los 5 ataques adversarios (A–E) contra `gate.cross_source_mismatch`.

Eliminar Sectors → producto muere (prueba Stage 1: Sectors es core data source).

Nota: `run.sh` también expone `./run.sh test` que corre todos los gates.
