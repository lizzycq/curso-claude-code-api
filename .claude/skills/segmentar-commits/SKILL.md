---
name: segmentar-commits
description: >-
  Reparte los cambios sin confirmar del repositorio en commits con una sola
  intención cada uno. Arranca del estado real (inyecta `git status -sb` y
  `git diff --stat`, no el diff completo), ordena los commits para que cada uno
  deje el repo en un estado comprobable, elige el prefijo de Conventional
  Commits por lo que hace el commit y no por el tipo de archivo, y enseña el
  reparto propuesto esperando aprobación antes de confirmar nada.
---

# segmentar-commits

Toma un árbol de trabajo con cambios mezclados y propone cómo partirlos en
commits limpios. **No confirma nada hasta que el usuario aprueba el reparto.**

## Estado real, inyectado al invocar

Antes de proponer nada se ejecutan y se leen, en este orden:

1. `git status -sb` — rama, upstream, y la lista de archivos modificados,
   añadidos, borrados y sin seguimiento.
2. `git diff --stat HEAD` — el resumen por archivo: cuántas líneas cambian en
   cada uno, sin el contenido.
3. `git stash list` y `git log --oneline -5` — para saber si hay trabajo
   escondido y sobre qué base se está.

Se parte de esa salida, **no de lo que la conversación supone que hay en el
árbol**. Si `git status -sb` sale vacío, no hay nada que segmentar: se dice y
se para.

Lo que **no** se inyecta es el `git diff` completo. Hace falta el mapa del
cambio —qué archivos, qué volumen, agrupados por zona del repo—, no su
contenido línea a línea. Si para decidir un límite entre commits se necesita
ver un fragmento concreto, se pide ese archivo puntual con `git diff -- <ruta>`,
no el diff entero.

## Procedimiento

1. **Inyectar el estado real** (sección de arriba).
2. **Agrupar los archivos por intención**, no por carpeta ni por tipo. Una
   intención es un cambio que se puede describir en una frase sin la palabra
   "y": "añade el endpoint X", "corrige el orden de Y", "renombra Z". Un mismo
   archivo puede quedar partido entre dos commits si mezcla dos intenciones
   (se anota que hará falta `git add -p`).
3. **Ordenar los commits** de forma que cada uno, aplicado sobre el anterior,
   deje el repositorio en un estado comprobable: compila, la suite pasa o
   falla solo por lo que ese commit aún no trae, el lint está limpio. Las
   dependencias primero (un helper antes del código que lo usa; una migración
   antes del endpoint que lee la tabla).
4. **Elegir el prefijo de Conventional Commits por lo que hace el commit**:
   - `feat:` añade una capacidad observable.
   - `fix:` corrige un comportamiento incorrecto.
   - `refactor:` cambia la forma sin cambiar el comportamiento.
   - `test:` añade o ajusta solo pruebas.
   - `docs:` cambia solo documentación o texto.
   - `chore:` andamiaje, configuración, dependencias, permisos.
   Un commit que **mueve** un test de sitio sin tocar producción es `test:` o
   `chore:`, no `feat:`, aunque el archivo sea `.py` de `app/`. Un commit que
   añade un endpoint es `feat:` aunque el grueso de las líneas esté en el
   archivo de tests. El prefijo describe el efecto, no la extensión.
5. **Redactar cada mensaje**: asunto imperativo en una línea (≤ ~72 car.);
   cuerpo con el porqué si no es obvio. Si el repo tiene una convención de pie
   (co-autoría, enlace de sesión), incluirla.
6. **Enseñar el reparto** como una tabla: nº de commit, prefijo + asunto,
   archivos (o `archivo (parcial)`), y una línea de "estado tras este commit".
   **Esperar aprobación.**
7. Tras el visto bueno, y solo entonces, aplicar los commits en orden
   (`git add` de las rutas de cada grupo, `git add -p` donde haya archivos
   partidos, `git commit`). Verificar con `git log --oneline` y `git status`
   que el árbol queda limpio.

## Límites

- No confirma, no hace `rebase`, no reescribe historia ya publicada, no hace
  `push`.
- No descarta ni recupera cambios (`checkout`, `restore`, `stash pop`) sin que
  el usuario lo pida.
- No arrastra a un commit archivos que no encajan en su intención: si algo
  sobra, se deja fuera y se dice.
- Si un archivo sin seguimiento parece ajeno al conjunto (artefacto, archivo
  temporal), se señala y se pregunta antes de incluirlo.
