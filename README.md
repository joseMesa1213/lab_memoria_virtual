# Laboratorio: Simulador de Memoria Virtual

Simulador de gestión de memoria virtual con **paginación de dos niveles**, **traducción VA → PA**, **manejo de fallos de página**, **swap** y tres **políticas de reemplazo**: **FIFO**, **LRU** y **CLOCK** (bonus). Está escrito en C++17.

- Espacio virtual de 32 bits: `PT1 (10b) | PT2 (10b) | Offset (12b)` con páginas de 4 KB
- Tamaño de página configurable (potencia de 2, de 1 KB a 1 MB). Los bits se reparten solos.
- Memoria física configurable (mínimo 256 KB y máximo 1 GB, múltiplo del tamaño de página)
- Tablas de nivel 2 creadas bajo demanda y liberadas cuando quedan vacías
- PTE con `frame`, `valid`, `accessed`, `dirty` y `swapped`
- Estadísticas: accesos, fallos, hit rate, reemplazos, swap-in/out, segfaults y tiempos
- Sin warnings (`-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror`) y sin fugas de memoria

> **Integrantes:** _(completar)_ · **Política asignada:** _(FIFO o LRU)_. El simulador implementa las dos y además CLOCK.

## Estructura

```
.
├── Makefile
├── include/                 Cabeceras (.hpp)
│   ├── address_layout.hpp   División PT1 | PT2 | Offset
│   ├── page_table.hpp       PageTableEntry, SecondLevelTable, PageTable
│   ├── physical_memory.hpp  Marcos, lista libre y dueño de cada marco
│   ├── backing_store.hpp    Swap (vpn → contenido de la página)
│   ├── virtual_allocator.hpp Regiones alloc/free (first-fit)
│   ├── replacement_policy.hpp Interfaz + fábrica
│   ├── fifo_policy.hpp · lru_policy.hpp · clock_policy.hpp · frame_list.hpp
│   ├── memory_manager.hpp   MMU: translate, handlePageFault, evict
│   ├── statistics.hpp · trace.hpp · simulator.hpp · config.hpp
├── src/                     Implementaciones (.cpp) y main.cpp
├── tools/gen_trace.cpp      Generador de cargas: seq, random, locality, matrix
├── tests/
│   ├── basico.txt           Ejemplo del enunciado
│   ├── belady.txt           Anomalía de Belady (páginas de 128 KB)
│   ├── liberacion.txt       free, reutilización, segfaults y errores de sintaxis
│   ├── swap.txt             Persistencia de datos a través de swap
│   ├── traduccion.txt       Descomposición de bits de la dirección
│   ├── secuencial.txt · aleatorio.txt · localidad.txt · matrices.txt
│   ├── referencia.py        Simulador de referencia independiente (oráculo)
│   └── run_tests.sh         33 pruebas automáticas
└── docs/
    ├── REPORTE.md · Reporte.pdf   Reporte de análisis
    ├── diagramas/           8 diagramas: .drawio editable + .svg + .png
    ├── graficas/            Gráficas de resultados + CSV con los datos
    └── scripts/             Scripts que generan diagramas y gráficas
```

## Compilación

Requisitos: `g++` o `clang++` con C++17 y `make`. Para las pruebas de referencia se necesita `python3`.

```bash
make            # compila vmsim y gen_trace
make clean      # borra binarios y objetos
```

## Uso

```bash
./vmsim [opciones] <archivo_trazas>

  -p, --policy <fifo|lru|clock|all>  política de reemplazo (defecto: fifo)
  -s, --page-size <tam>              tamaño de página (defecto: 4K)
  -m, --memory <tam>                 memoria física, mínimo 256K (defecto: 256K)
  -v, --verbose                      muestra la traducción de cada operación
  -c, --csv                          salida CSV (para scripts o gráficas)
  -h, --help                         ayuda
```

Los tamaños aceptan sufijos `K`, `M` y `G`. Las direcciones y los valores pueden ir en decimal o en hexadecimal (`0x...`).

### Formato del archivo de entrada

```
# comentario
alloc <bytes>           reserva una región (se redondea a páginas) y muestra su dirección base
write <va> <valor>      escribe un byte (0-255) en la dirección virtual
read  <va>              lee un byte de la dirección virtual
free  <va>              libera la región que empieza en va
```

Ejemplo (`tests/basico.txt`):

```
alloc 8192
write 0 42
write 4096 99
read 0
read 4096
```

```
$ ./vmsim -v tests/basico.txt
[L   2] alloc 8192 -> región en 0x00000000
[L   3] write 0x00000000 <-  42  (pt1=   0, pt2=   0, off=0x000) -> PA 0x00000000  marco    0  FALLO
[L   4] write 0x00001000 <-  99  (pt1=   0, pt2=   1, off=0x000) -> PA 0x00001000  marco    1  FALLO
[L   5] read  0x00000000         (pt1=   0, pt2=   0, off=0x000) -> PA 0x00000000  marco    0  valor=42  HIT
[L   6] read  0x00001000         (pt1=   0, pt2=   1, off=0x000) -> PA 0x00001000  marco    1  valor=99  HIT
==================== Estadísticas finales ====================
Política: FIFO
Tamaño de página: 4096 bytes
Marcos físicos: 64 (256 KB)
--------------------------------------------------------------
Total de accesos: 4 (lecturas 2, escrituras 2)
Total fallos de página: 2
Hit rate: 50.00%
Total reemplazos: 0
...
```

### Targets del Makefile

| Target | Descripción |
|---|---|
| `make all` | Compila `vmsim` y `gen_trace` |
| `make run` | Ejecuta con `POLICY`, `PAGE`, `MEM` y `TRACE` (por ejemplo `make run POLICY=lru TRACE=tests/localidad.txt MEM=512K`) |
| `make compare` | Corre FIFO, LRU y CLOCK sobre la misma traza y muestra una tabla comparativa |
| `make test` | Corre las 33 pruebas automáticas |
| `make traces` | Regenera las trazas grandes con `gen_trace` |
| `make sanitize` | Recompila con AddressSanitizer + UBSan y corre las pruebas |
| `make leaks` | Verifica fugas con `valgrind` (Linux) o `leaks` (macOS) |
| `make clean` | Limpia |

### Ejemplos

```bash
make compare TRACE=tests/localidad.txt MEM=512K
./vmsim -p all -s 128K -m 384K tests/belady.txt      # FIFO: 9 fallos
./vmsim -p all -s 128K -m 512K tests/belady.txt      # FIFO: 10 fallos (Belady)
./gen_trace locality 1024 100000 42 > mi_traza.txt
./vmsim -c -p all -m 1M mi_traza.txt
```

## Verificación

- `make test`: 33 pruebas. Revisan el ejemplo del enunciado, la anomalía de Belady, `free` y la reutilización de regiones, los segfaults, los errores de sintaxis, la persistencia en swap y la descomposición de bits. También comparan el número de fallos con `tests/referencia.py`, un simulador independiente, en 4 trazas con 64, 128 y 256 marcos.
- `make sanitize`: las 33 pruebas pasan con ASan y UBSan.
- `make leaks`: `0 leaks for 0 total leaked bytes`. Toda la memoria dinámica es RAII (`std::vector`, `std::unique_ptr`, `std::map`) y no hay `new` ni `delete` manuales.

## Documentación

- [Reporte de análisis](docs/REPORTE.md) ([PDF](docs/Reporte.pdf))
- Diagramas en `docs/diagramas/`. Los `.drawio` se abren y editan en [app.diagrams.net](https://app.diagrams.net).
- Para regenerar gráficas y diagramas: `python3 docs/scripts/graficas.py` y `python3 docs/scripts/diagramas.py` (requieren `rsvg-convert`).
