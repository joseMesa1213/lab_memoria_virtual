import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drawio import (B, BLUE, GRAY, GREEN, I, Line, M, ORANGE, PURPLE, RED, WHITE, YELLOW, Diagram)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diagramas")


def arquitectura():
    d = Diagram("01_arquitectura", 1010, 660, "Arquitectura del simulador",
                "Componentes, responsabilidades y flujo de datos entre módulos")
    traza = d.box(30, 90, 180, 56, [B("Archivo de trazas"), M("alloc | write | read | free", size=10)], GRAY)
    cli = d.box(30, 190, 180, 56, [B("Línea de comandos"), M("-p -s -m -v -c", size=11)], GRAY)
    parser = d.box(260, 90, 200, 56, [B("trace.cpp"), Line("loadTrace() → Command[]", size=11)], YELLOW)
    config = d.box(260, 190, 200, 56, [B("config.cpp"), Line("parseArguments() / validateConfig()", size=10)],
                   YELLOW)
    sim = d.box(520, 130, 200, 76, [B("Simulator"), Line("run() · execute()", size=11),
                                    Line("mide tiempo total", size=11)], ORANGE)
    report = d.box(780, 130, 200, 76, [B("Salida"), Line("reporte · CSV · traza -v", size=11),
                                       Line("printReport / printCsvRow", size=10)], GRAY)
    d.edge(traza, parser)
    d.edge(cli, config)
    d.edge(parser, sim, "r", (0, 0.3))
    d.edge(config, sim, "r", (0, 0.7))
    d.edge(sim, report)

    mm = d.container(40, 290, 940, 350, [B("MemoryManager  (MMU + manejador de memoria del SO)")], BLUE, header=30)
    d.edge(sim, mm, "b", (0.6, 0), label=M("read / write / alloc / free", size=11))

    alloc = d.box(70, 350, 190, 70, [B("VirtualAllocator"), Line("regiones [inicio, tamaño)", size=11),
                                     Line("first-fit alineado a página", size=11)], GREEN)
    layout = d.box(70, 470, 190, 70, [B("AddressLayout"), M("PT1 | PT2 | Offset", size=11),
                                      Line("bits según tamaño de página", size=10)], GREEN)
    table = d.box(340, 350, 200, 70, [B("PageTable"), Line("directorio 1024 → tablas nivel 2", size=11),
                                      Line("creación bajo demanda", size=11)], BLUE)
    phys = d.box(340, 510, 200, 70, [B("PhysicalMemory"), Line("bytes · FrameInfo · lista libre", size=11)],
                 YELLOW)
    policy = d.box(620, 350, 210, 70, [B("ReplacementPolicy"), M("FIFO | LRU | CLOCK", size=11),
                                       Line("selectVictim()", size=11)], PURPLE)
    swap = d.cylinder(640, 480, 170, 110, [B("BackingStore"), Line("swap: vpn → página", size=11)], GRAY)
    stats = d.box(860, 350, 100, 70, [B("Statistics"), Line("fallos, hits,", size=10), Line("reemplazos", size=10)],
                  RED)

    d.edge(alloc, table, label=Line("contains(va)", size=10))
    d.edge(layout, table, "r", (0, 0.8), via=[(300, 505), (300, 406)], label=Line("split(va)", size=10),
           label_at=(300, 470))
    d.edge(table, phys, "b", "t", label=Line("PTE.frame", size=10))
    d.edge(policy, table, "l", "r", label=Line("víctima", size=10))
    d.edge(phys, swap, "r", (0, 0.5), label=Line("swap-out", size=10), label_at=(590, 520))
    d.edge(swap, phys, (0, 0.72), (1, 0.8), label=Line("swap-in", size=10), label_at=(590, 566))
    d.text(560, 600, 400, 30, I("translate() · handlePageFault() · obtainFrame() · evict()", size=11,
                                color="#555555"), align="right")
    d.edge(policy, stats, "r", "l", dashed=True, end="openthin")
    d.save(OUT)


def direccion():
    d = Diagram("02_direccion_virtual", 1000, 660, "Dirección virtual de 32 bits (páginas de 4 KB)",
                "Descomposición PT1 | PT2 | Offset y ejemplo de traducción de 0x00403ABC")
    unit = 26
    x0 = 84
    fields = [("PT1", 10, 31, 22, BLUE, "0000000001", "índice nivel 1 (1024 entradas)"),
              ("PT2", 10, 21, 12, GREEN, "0000000011", "índice nivel 2 (1024 entradas)"),
              ("Offset", 12, 11, 0, YELLOW, "101010111100", "desplazamiento en la página")]
    x = x0
    cells = []
    for name, bits, hi, lo, colors, sample, desc in fields:
        w = bits * unit
        d.text(x, 84, 40, 18, Line(str(hi), size=11, color="#555555"), align="left")
        d.text(x + w - 40, 84, 40, 18, Line(str(lo), size=11, color="#555555"), align="right")
        cell = d.rect(x, 104, w, 50, [B(f"{name}  ({bits} bits)"), Line(desc, size=11)], colors)
        d.rect(x, 154, w, 34, M(sample, size=14), ("#ffffff", colors[1]))
        cells.append(cell)
        x += w
    d.text(20, 104, 60, 50, Line("VA", size=14, bold=True))
    d.text(8, 154, 76, 34, Line("0x00403ABC", size=10, mono=True))

    results = [
        (d.box(90, 250, 220, 56, [B("PT1 = 0x001 = 1"), M("va >> 22", size=11)], BLUE), cells[0]),
        (d.box(390, 250, 220, 56, [B("PT2 = 0x003 = 3"), M("(va >> 12) & 0x3FF", size=11)], GREEN), cells[1]),
        (d.box(690, 250, 220, 56, [B("Offset = 0xABC"), M("va & 0xFFF", size=11)], YELLOW), cells[2]),
    ]
    for box, cell in results:
        cx = cell.x + cell.w / 2
        d.line([(cx, 188), (cx, 220), (box.x + box.w / 2, 220), (box.x + box.w / 2, 250)])
    dir_box = d.box(90, 350, 220, 60, [B("directorio[1]"), Line("→ tabla de nivel 2 (existe o se crea)", size=10)],
                    BLUE)
    pte = d.box(390, 350, 220, 60, [B("tabla2[3] = PTE"), M("frame=0 V=1 A=1 D=1 S=0", size=11)], GREEN)
    pa = d.box(690, 350, 220, 60, [B("PA = 0x00000ABC"), M("(frame << 12) | offset", size=11)], ORANGE)
    d.edge(results[0][0], dir_box, "b", "t")
    d.edge(results[1][0], pte, "b", "t")
    d.edge(results[2][0], pa, "b", "t")
    d.edge(dir_box, pte)
    d.edge(pte, pa, label=Line("frame", size=10))

    d.text(60, 440, 880, 24, [B("Tamaño de página configurable (AddressLayout)", size=13)], align="left")
    d.text(60, 464, 880, 22, M("offsetBits = log2(pageSize)   pt2Bits = (32 - offsetBits) / 2   "
                               "pt1Bits = 32 - offsetBits - pt2Bits", size=12), align="left")
    headers = ["Página", "PT1", "PT2", "Offset", "Entradas L1 × L2"]
    rows = [["1 KB", "11", "11", "10", "2048 × 2048"], ["4 KB", "10", "10", "12", "1024 × 1024"],
            ["16 KB", "9", "9", "14", "512 × 512"], ["64 KB", "8", "8", "16", "256 × 256"],
            ["1 MB", "6", "6", "20", "64 × 64"]]
    widths = [110, 80, 80, 90, 170]
    y = 496
    x = 60
    for header, w in zip(headers, widths):
        d.rect(x, y, w, 26, B(header, size=11), GRAY)
        x += w
    for r, row in enumerate(rows):
        x = 60
        for value, w in zip(row, widths):
            fill = ("#eef4fc", "#6c8ebf") if row[0] == "4 KB" else ("#ffffff", "#999999")
            d.rect(x, y + 26 + r * 22, w, 22, M(value, size=11), fill)
            x += w
    d.box(640, 496, 300, 136, [B("Por qué dos niveles"), Line("Una tabla plana de 2²⁰ entradas ocupa", size=11),
                               Line("memoria aunque el proceso use poco.", size=11),
                               Line("Con dos niveles solo existen las tablas", size=11),
                               Line("de nivel 2 de las regiones tocadas.", size=11)], BLUE)
    d.save(OUT)


def tabla_dos_niveles():
    d = Diagram("03_tabla_dos_niveles", 1120, 720, "Tabla de páginas de dos niveles",
                "Directorio fijo de 1024 punteros; tablas de nivel 2 creadas solo para las regiones tocadas")
    va_pt1 = d.rect(150, 90, 110, 40, [B("PT1 = 1")], BLUE)
    va_pt2 = d.rect(260, 90, 110, 40, [B("PT2 = 3")], GREEN)
    va_off = d.rect(370, 90, 130, 40, [B("Offset = 0xABC")], YELLOW)
    d.text(20, 90, 125, 40, [B("VA", size=12), M("0x00403ABC", size=12)])

    d.container(40, 200, 200, 230, [B("Directorio (nivel 1)"), Line("vector<unique_ptr<...>>", size=10)], BLUE,
                header=40)
    dir_rows = []
    labels = [("0", "→ tabla", True), ("1", "→ tabla", True), ("2", "nullptr", False), ("…", "", False),
              ("1023", "nullptr", False)]
    for i, (idx, target, live) in enumerate(labels):
        colors = ("#dae8fc", "#6c8ebf") if idx == "1" else ("#ffffff", "#999999")
        row = d.rect(40, 240 + i * 38, 200, 38, [M(f"[{idx:>4}]  {target}", size=12,
                                                    color="#000000" if live else "#888888")], colors,
                     align="left")
        dir_rows.append(row)
    d.edge(va_pt1, dir_rows[1], "b", "l", via=[(205, 165), (22, 165), (22, 297)], label=Line("índice PT1", size=10),
           label_at=(110, 165))

    l2box = d.container(330, 170, 330, 300, [B("Tabla de nivel 2  (dir[1])"), Line("1024 × PageTableEntry", size=10)],
                GREEN, header=40)
    d.rect(330, 210, 330, 26, M(" idx  frame  V  A  D  S", size=12, bold=True), GRAY, align="left")
    l2 = []
    entries = [("0", "  5", "1", "0", "0", "0"), ("1", "  -", "0", "0", "0", "1"), ("2", "  -", "0", "0", "0", "0"),
               ("3", "  0", "1", "1", "1", "0"), ("…", "", "", "", "", ""), ("1023", "  -", "0", "0", "0", "0")]
    for i, (idx, frame, v, a, dd, s) in enumerate(entries):
        colors = ("#d5e8d4", "#82b366") if idx == "3" else ("#ffffff", "#999999")
        text = f"{idx:>4}  {frame:>5}  {v}  {a}  {dd}  {s}" if frame else f"{idx:>4}"
        l2.append(d.rect(330, 236 + i * 36, 330, 36, M(text, size=12), colors, align="left"))
    d.edge(dir_rows[1], l2[0], "r", (0, 0.0), via=[(290, 297), (290, 236)])
    d.edge(va_pt2, l2box, "b", (20 / 330, 0), via=[(315, 150), (350, 150)])
    d.text(360, 140, 200, 20, Line("índice PT2 = 3 → fila 3", size=10), align="left")
    d.container(760, 130, 170, 360, [B("Memoria física"), Line("64 marcos (256 KB)", size=10)], YELLOW, header=40)
    frames = []
    names = [("0", "vpn 0x00403", True), ("1", "vpn 0x00000", False), ("2", "libre", False), ("…", "", False),
             ("5", "vpn 0x00400", False), ("…", "", False), ("63", "libre", False)]
    for i, (idx, owner, hot) in enumerate(names):
        colors = ("#ffe6cc", "#d79b00") if hot else ("#ffffff", "#999999")
        frames.append(d.rect(760, 170 + i * 45, 170, 45, [M(f"marco {idx}", size=11, bold=hot),
                                                          Line(owner, size=10, color="#555555")], colors))
    d.edge(l2[3], frames[0], "r", (0, 0.7), via=[(710, 364), (710, 201.5)], label=Line("frame = 0", size=10),
           label_at=(710, 290))
    d.edge(va_off, frames[0], "r", (0, 0.25), via=[(735, 110), (735, 181.25)], label=Line("+ offset 0xABC", size=10),
           label_at=(560, 110))

    swap = d.cylinder(970, 300, 130, 130, [B("BackingStore"), Line("vpn 0x00401", size=10), Line("(dir1, idx1)", size=10)],
                      GRAY)
    d.edge(frames[4], swap, "r", (0, 0.35), label=Line("swap-out (D=1)", size=10), dashed=True, label_at=(1035, 282))
    d.edge(swap, l2box, "b", (0.5, 1), via=[(1035, 520), (495, 520)], dashed=True,
           label=Line("fila 1 tiene S=1: su copia vigente está en swap → swap-in al fallar", size=10),
           label_at=(760, 520))

    d.box(40, 560, 380, 130, [B("PageTableEntry"), M("frame  número de marco físico", size=11),
                              M("V  valid: cargada en un marco", size=11),
                              M("A  accessed: referenciada (CLOCK)", size=11),
                              M("D  dirty: escrita desde que se cargó", size=11),
                              M("S  swapped: tiene copia en swap", size=11)], GREEN, align="left")
    d.box(450, 560, 330, 130, [B("Costo de memoria"), Line("Tabla plana: 2²⁰ PTE siempre", size=11),
                               Line("Dos niveles: 1024 punteros + 1024 PTE", size=11),
                               Line("por cada región de 4 MB que se use", size=11),
                               Line("PageTable::compact() libera tablas vacías", size=11)], BLUE)
    d.box(810, 560, 290, 130, [B("PA = (frame << offsetBits) | offset"), M("= (0 << 12) | 0xABC", size=11),
                               M("= 0x00000ABC", size=12, bold=True)], ORANGE)
    d.save(OUT)


def flujo_traduccion():
    d = Diagram("04_flujo_traduccion", 900, 1360, "Flujo de traducción VA → PA y manejo de fallos",
                "MemoryManager::translate() → handlePageFault() → obtainFrame() → evict()")
    start = d.ellipse(330, 80, 220, 54, [B("read(va) / write(va, v)")], GREEN)
    q1 = d.rhombus(315, 165, 250, 110, ["¿va pertenece a una", "región asignada?"])
    seg = d.box(650, 190, 210, 60, [B("SEGFAULT"), M("segmentationFaults++", size=11)], RED)
    count = d.box(340, 310, 200, 50, [M("reads++ / writes++", size=12)], BLUE)
    resolve = d.box(315, 390, 250, 60, [M("pageTable.resolve(va)", size=12),
                                        Line("crea la tabla de nivel 2 si no existe", size=11)], BLUE)
    q2 = d.rhombus(340, 480, 200, 100, [B("¿PTE.valid?")])
    hit = d.box(80, 500, 200, 60, [B("HIT"), M("policy.onAccess(frame)", size=11)], GREEN)
    fault = d.box(340, 615, 200, 56, [B("FALLO DE PÁGINA"), M("pageFaults++", size=11)], RED)
    q3 = d.rhombus(340, 705, 200, 100, ["¿marco libre?"])
    evict = d.box(610, 705, 260, 110, [B("Reemplazo"), M("v = policy.selectVictim()", size=11),
                                       M("si PTE(v).dirty: swap.store", size=11), M("PTE(v).valid = 0", size=11),
                                       M("releaseFrame(v); replacements++", size=11)], ORANGE, align="left")
    acquire = d.box(340, 845, 200, 50, [M("acquireFrame(vpn)", size=12)], YELLOW)
    q4 = d.rhombus(340, 930, 200, 100, ["¿PTE.swapped?"])
    load = d.box(80, 950, 200, 60, [M("swap.load(vpn, marco)", size=11), M("swapIns++", size=11)], PURPLE)
    zero = d.box(600, 950, 200, 60, [M("zeroFrame(marco)", size=11), M("zeroFills++", size=11)], GRAY)
    bind = d.box(315, 1060, 250, 60, [M("frame=marco; valid=1; dirty=0", size=11), M("policy.onLoad(marco)", size=11)],
                 BLUE)
    finish = d.box(315, 1160, 250, 60, [M("accessed = 1; si write: dirty = 1", size=11),
                                        M("PA = frame << offBits | offset", size=11)], BLUE)
    end = d.ellipse(330, 1260, 220, 54, [B("leer / escribir byte en PA")], GREEN)

    d.edge(start, q1, "b", "t")
    d.edge(q1, seg, "r", "l", label=B("No", size=11))
    d.edge(q1, count, "b", "t", label=B("Sí", size=11))
    d.edge(count, resolve, "b", "t")
    d.edge(resolve, q2, "b", "t")
    d.edge(q2, hit, "l", "r", label=B("Sí", size=11))
    d.edge(q2, fault, "b", "t", label=B("No", size=11))
    d.edge(fault, q3, "b", "t")
    d.edge(q3, acquire, "b", "t", label=B("Sí", size=11))
    d.edge(q3, evict, "r", (0, 0.5), label=B("No", size=11))
    d.edge(evict, acquire, "b", "r", via=[(740, 870)])
    d.edge(acquire, q4, "b", "t")
    d.edge(q4, load, "l", "r", label=B("Sí", size=11))
    d.edge(q4, zero, "r", "l", label=B("No", size=11))
    d.edge(load, bind, "b", "l", via=[(180, 1090)])
    d.edge(zero, bind, "b", "r", via=[(700, 1090)])
    d.edge(hit, finish, "l", "l", via=[(40, 530), (40, 1190)])
    d.edge(bind, finish, "b", "t")
    d.edge(finish, end, "b", "t")
    d.text(610, 820, 260, 20, I("tiempo medido en faultTime", size=10, color="#555555"))
    d.save(OUT)


def secuencia_fallo():
    d = Diagram("05_secuencia_fallo", 1260, 930, "Diagrama de secuencia: write con fallo de página y reemplazo",
                "Memoria llena, la víctima está sucia y la página pedida tiene copia en swap")
    actors = ["Simulator", "MemoryManager", "VirtualAllocator", "PageTable", "ReplacementPolicy", "PhysicalMemory",
              "BackingStore"]
    colors = [ORANGE, BLUE, GREEN, BLUE, PURPLE, YELLOW, GRAY]
    xs = [90, 270, 450, 620, 800, 990, 1170]
    for name, x, colors_ in zip(actors, xs, colors):
        d.box(x - 80, 76, 160, 40, B(name, size=12), colors_)
        if name == "MemoryManager":
            d.line([(x, 116), (x, 140)], dashed=True, end="none", color="#999999")
            d.line([(x, 880), (x, 900)], dashed=True, end="none", color="#999999")
        else:
            d.line([(x, 116), (x, 900)], dashed=True, end="none", color="#999999")
    d.rect(264, 140, 12, 740, None, ("#dae8fc", "#6c8ebf"))
    d.frame(290, 440, 960, 235, [B("alt  [no hay marcos libres]", size=11)], dashed=False)

    def call(y, a, b, text, dashed=False):
        x1, x2 = xs[a], xs[b]
        if a == 1:
            x1 += 6
        if b == 1:
            x2 += 6 if x1 > x2 else -6
        end = "openthin" if dashed else "classic"
        d.line([(x1, y), (x2, y)], label=M(text, size=11) if not dashed else I(text, size=11), dashed=dashed, end=end,
               label_at=((x1 + x2) / 2, y - 11))

    call(150, 0, 1, "write(va, valor)")
    call(190, 1, 2, "contains(va)")
    call(220, 2, 1, "true", True)
    call(260, 1, 3, "resolve(va)")
    call(290, 3, 1, "PTE& (valid = 0, swapped = 1)", True)
    d.line([(276, 330), (330, 330), (330, 360), (276, 360)], label=M("handlePageFault()", size=11),
           label_at=(390, 345))
    call(395, 1, 5, "acquireFrame(vpn)")
    call(420, 5, 1, "nullopt", True)
    call(475, 1, 4, "selectVictim(probe)")
    call(505, 4, 1, "marco víctima v", True)
    call(545, 1, 3, "find(pageBase(ownerOf(v)))")
    call(575, 3, 1, "PTE víctima (dirty = 1)", True)
    call(615, 1, 6, "store(vpn víctima, frameData(v))")
    call(655, 1, 5, "releaseFrame(v)")
    call(715, 1, 5, "acquireFrame(vpn)")
    call(745, 5, 1, "marco v", True)
    call(785, 1, 6, "load(vpn, frameData(v))")
    call(815, 6, 1, "true  (swapIns++)", True)
    call(850, 1, 4, "onLoad(v)")
    call(885, 1, 0, "AccessResult", True)
    d.save(OUT)


def clases():
    d = Diagram("06_clases", 1360, 1120, "Diagrama de clases", "Estructuras de datos y relaciones del simulador")
    config = d.uml_class(30, 80, 250, "Config", ["pageSize: uint32", "physicalMemory: uint64",
                                                 "policies: vector<PolicyKind>", "verbose, csv: bool",
                                                 "inputPath: string"],
                         ["parseArguments(argc, argv)", "validateConfig(config)"], YELLOW, "struct")
    sim = d.uml_class(360, 80, 280, "Simulator", ["- config_: Config", "- manager_: MemoryManager"],
                      ["+ run(trace, log): RunSummary", "- execute(command, log)", "- logAccess(cmd, result, log)"],
                      ORANGE)
    trace = d.uml_class(720, 80, 270, "Trace", ["commands: vector<Command>", "errors: vector<TraceError>"],
                        ["loadTrace(path): Trace", "parseTrace(istream): Trace"], YELLOW, "struct")
    command = d.uml_class(1070, 80, 250, "Command", ["type: CommandType", "first: uint64", "second: uint64",
                                                     "line: size_t"], [], YELLOW, "struct")
    stats = d.uml_class(1070, 290, 250, "Statistics", ["reads, writes: uint64", "pageFaults, replacements",
                                                       "swapOuts, swapIns, zeroFills", "segmentationFaults",
                                                       "faultTime, totalTime: ns"],
                        ["accesses(), hits()", "hitRate(): double"], RED, "struct")
    mm = d.uml_class(360, 330, 330, "MemoryManager", ["- layout_: AddressLayout", "- pageTable_: PageTable",
                                                      "- physical_: PhysicalMemory", "- swap_: BackingStore",
                                                      "- allocator_: VirtualAllocator",
                                                      "- policy_: unique_ptr<ReplacementPolicy>",
                                                      "- stats_: Statistics"],
                     ["+ allocate(bytes): optional<uint32>", "+ release(va): optional<uint64>",
                      "+ read(va): AccessResult", "+ write(va, value): AccessResult",
                      "- translate(va, kind): AccessResult", "- handlePageFault(va, pte, result)",
                      "- obtainFrame(vpn, result): uint32", "- evict(frame, result)"], BLUE)
    layout = d.uml_class(30, 330, 250, "AddressLayout", ["- pageSize_, offsetBits_", "- pt1Bits_, pt2Bits_"],
                         ["+ split(va): VirtualAddressParts", "+ pageNumber(va): uint32", "+ pageBase(vpn): uint32",
                          "+ physicalAddress(frame, off)"], GREEN)
    alloc = d.uml_class(770, 330, 250, "VirtualAllocator", ["- regions_: map<uint32, uint64>", "- reserved_: uint64"],
                        ["+ allocate(bytes): optional<uint32>", "+ release(start): optional<uint64>",
                         "+ contains(va): bool"], GREEN)
    table = d.uml_class(30, 700, 290, "PageTable", ["- directory_: vector<unique_ptr<", "      SecondLevelTable>>",
                                                    "- live_, created_, released_"],
                        ["+ find(va): PageTableEntry*", "+ resolve(va): PageTableEntry&", "+ compact(va)"], BLUE)
    second = d.uml_class(30, 930, 290, "SecondLevelTable", ["- entries_: vector<PageTableEntry>"],
                         ["+ entry(index): PageTableEntry&", "+ empty(): bool"], BLUE)
    pte = d.uml_class(380, 930, 220, "PageTableEntry", ["frame: uint32", "valid, accessed: bool",
                                                        "dirty, swapped: bool"], ["inUse(): bool"], BLUE, "struct")
    phys = d.uml_class(380, 700, 290, "PhysicalMemory", ["- bytes_: vector<uint8>", "- frames_: vector<FrameInfo>",
                                                         "- freeList_: vector<uint32>"],
                       ["+ acquireFrame(vpn): optional<uint32>", "+ releaseFrame(frame)", "+ ownerOf(frame): uint32",
                        "+ frameData(frame): uint8*"], YELLOW)
    swap = d.uml_class(720, 700, 280, "BackingStore", ["- pages_: unordered_map<", "      uint32, vector<uint8>>"],
                       ["+ store(vpn, data)", "+ load(vpn, dest): bool", "+ discard(vpn)"], GRAY)
    policy = d.uml_class(1070, 560, 260, "ReplacementPolicy", [],
                         ["+ onLoad(frame)", "+ onAccess(frame)", "+ onRelease(frame)",
                          "+ selectVictim(probe): uint32", "+ name(): string"], PURPLE, "interface")
    fifo = d.uml_class(1070, 800, 120, "FifoPolicy", ["- queue_"], [], PURPLE)
    lru = d.uml_class(1210, 800, 120, "LruPolicy", ["- recency_"], [], PURPLE)
    clock = d.uml_class(1070, 900, 260, "ClockPolicy", ["- occupied_: vector<bool>", "- hand_, loaded_: uint32"], [],
                        PURPLE)
    frame_list = d.uml_class(720, 930, 280, "FrameList", ["- order_: list<uint32>",
                                                          "- position_: vector<iterator>", "- tracked_: vector<bool>"],
                             ["+ pushBack, moveToBack", "+ remove, popFront"], PURPLE)

    comp = dict(start="diamond", end="none")
    d.edge(sim, config, "l", "r", **comp)
    d.edge(sim, trace, "r", "l", dashed=True, end="openthin", label=I("usa", size=10))
    d.edge(trace, command, "r", "l", start="diamond", end="none", label=Line("1..*", size=10))
    d.edge(sim, mm, "b", "t", **comp)
    d.edge(mm, layout, (0, 0.12), "r", **comp)
    d.edge(mm, alloc, (1, 0.12), "l", **comp)
    my = mm.y + mm.h * 0.05
    sy = stats.y + stats.h * 0.5
    d.edge(mm, stats, (1, 0.05), (0, 0.5), via=[(730, my), (730, 310), (1045, 310), (1045, sy)], **comp)
    d.edge(mm, table, (0.1, 1), "t", via=[(393, 670), (175, 670)], **comp)
    d.edge(mm, phys, (0.45, 1), (0.5, 0), via=[(508.5, 690), (525, 690)], **comp)
    d.edge(mm, swap, (0.8, 1), "t", via=[(624, 670), (860, 670)], **comp)
    py = policy.y + policy.h * 0.3
    d.edge(mm, policy, (1, 0.5), (0, 0.3), via=[(1040, mm.y + mm.h / 2), (1040, py)], start="diamond", end="none")
    d.edge(table, second, "b", "t", start="diamond", end="none", label=Line("0..1024", size=10))
    d.edge(second, pte, "r", "l", start="diamond", end="none", label=Line("1024", size=10))
    d.edge(fifo, policy, "t", (0.25, 1), dashed=True, end="open")
    d.edge(lru, policy, "t", (0.75, 1), dashed=True, end="open")
    d.edge(clock, policy, "r", (1, 0.5), via=[(1345, clock.y + clock.h / 2), (1345, policy.y + policy.h / 2)],
           dashed=True, end="open")
    fy = fifo.y + fifo.h / 2
    d.edge(fifo, frame_list, "l", (0.8, 0), via=[(1040, fy), (1040, 905), (944, 905)], start="diamond", end="none")
    d.edge(lru, frame_list, "b", (0.95, 0), via=[(1270, 878), (1052, 878), (1052, 915), (986, 915)],
           start="diamond", end="none")
    d.text(30, 1080, 900, 24, [Line("◆ composición (dueño del ciclo de vida)    - - ▷ realización de interfaz    "
                                    "- - > dependencia", size=11, color="#555555")], align="left")
    d.save(OUT)


def politicas():
    d = Diagram("07_politicas", 1300, 640, "Políticas de reemplazo: estructuras de datos",
                "Todas las operaciones son O(1) salvo el barrido de CLOCK (O(n) amortizado)")
    d.container(30, 80, 760, 250, [B("FIFO  (FifoPolicy → FrameList)")], BLUE)
    d.container(30, 350, 760, 270, [B("LRU  (LruPolicy → FrameList)")], ORANGE)
    d.container(820, 80, 450, 540, [B("CLOCK  (ClockPolicy, segunda oportunidad)")], GREEN)

    def chain(y, items, colors, head_label, tail_label):
        nodes = []
        for i, (frame, vpn) in enumerate(items):
            nodes.append(d.box(70 + i * 140, y, 110, 50, [B(f"marco {frame}", size=12), M(vpn, size=10)], colors))
        for a, b in zip(nodes, nodes[1:]):
            d.edge(a, b, "r", "l", start="classic", end="classic")
        d.text(40, y - 34, 180, 20, Line(head_label, size=11, bold=True), align="left")
        d.text(540, y - 34, 240, 20, Line(tail_label, size=11, bold=True), align="right")
        return nodes

    fifo = chain(160, [("3", "vpn 0x010"), ("0", "vpn 0x002"), ("7", "vpn 0x0A1"), ("1", "vpn 0x033"),
                       ("5", "vpn 0x004")], BLUE, "frente = más antigua", "final = más reciente")
    d.text(40, 225, 240, 36, [M("selectVictim(): popFront()", size=11)], align="left")
    d.text(420, 225, 360, 36, [M("onLoad(f): pushBack(f)", size=11)], align="right")
    d.text(40, 262, 740, 60, [Line("onAccess(): no hace nada → no aprovecha la localidad; una página muy usada",
                                   size=11),
                              Line("puede expulsarse solo por ser vieja. Sufre la anomalía de Belady.", size=11),
                              M("position_[marco] guarda el iterador → onRelease() en O(1)", size=11)],
           align="left")

    lru = chain(430, [("3", "vpn 0x010"), ("0", "vpn 0x002"), ("7", "vpn 0x0A1"), ("1", "vpn 0x033"),
                      ("5", "vpn 0x004")], ORANGE, "frente = LRU (víctima)", "final = MRU")
    d.edge(lru[1], lru[4], "b", "b", via=[(265, 505), (685, 505)], dashed=True,
           label=M("onAccess(0): splice al final", size=11), label_at=(475, 505))
    d.text(40, 520, 740, 90, [M("selectVictim(): popFront()     onLoad(f): pushBack(f)     onAccess(f): moveToBack(f)",
                                size=11),
                              Line("std::list + vector<iterator>: mover un nodo al final es O(1) sin recorrer la lista.",
                                   size=11),
                              Line("Es un algoritmo de pila: con más marcos nunca produce más fallos.", size=11)],
           align="left")

    import math
    cx, cy, r = 1045, 330, 150
    bits = [1, 0, 1, 1, 0, 1, 0, 1]
    owners = ["0x010", "0x002", "0x0A1", "0x033", "0x004", "0x07F", "0x120", "0x055"]
    for i in range(8):
        angle = -math.pi / 2 + i * 2 * math.pi / 8
        x = cx + r * math.cos(angle) - 45
        y = cy + r * math.sin(angle) - 25
        colors = RED if i == 1 else (GREEN if bits[i] else GRAY)
        d.box(x, y, 90, 50, [B(f"marco {i}", size=11), M(f"A={bits[i]} {owners[i]}", size=10)], colors)
    d.ellipse(cx - 30, cy - 30, 60, 60, [B("hand", size=11)], YELLOW)
    d.line([(cx, cy - 30), (cx, cy - r + 25)], width=2, label=None)
    d.text(cx - 128, cy - 100, 120, 20, Line("posición actual", size=10, color="#555555"), align="right")
    d.text(840, 520, 420, 90, [M("mientras true:", size=11), M("  si A[hand] = 1: A = 0; hand++", size=11),
                               M("  si A[hand] = 0: víctima = hand; hand++", size=11),
                               Line("marco 0 pierde su bit y marco 1 (A=0) es la víctima.", size=11)],
           align="left")
    d.save(OUT)


def estados():
    d = Diagram("08_estados_pagina", 1020, 560, "Ciclo de vida de una página virtual",
                "Estados según los bits de la PTE y la región del VirtualAllocator")
    init = d.ellipse(40, 250, 24, 24, None, ("#000000", "#000000"))
    none = d.box(100, 232, 150, 60, [B("No asignada"), Line("fuera de toda región", size=10)], GRAY)
    d.container(300, 80, 700, 450, [B("Región asignada")], BLUE)
    assigned = d.box(330, 280, 170, 64, [B("Reservada"), M("PTE vacía o sin tabla", size=10)], WHITE)
    clean = d.box(600, 140, 170, 64, [B("En memoria limpia"), M("V=1 D=0", size=11)], GREEN)
    dirty = d.box(600, 420, 170, 64, [B("En memoria sucia"), M("V=1 D=1", size=11)], ORANGE)
    swapped = d.box(820, 280, 160, 64, [B("En swap"), M("V=0 S=1", size=11)], PURPLE)
    d.edge(init, none, "r", "l")
    d.edge(none, assigned, "r", "l", via=[(275, 262), (275, 312)], label=M("alloc", size=11), label_at=(275, 287))
    d.edge(assigned, clean, "t", (0, 0.4), via=[(415, 165.6)], label=Line("read: fallo + zero-fill", size=10),
           label_at=(470, 165))
    d.edge(assigned, dirty, "b", (0, 0.5), via=[(415, 452)], label=Line("write: fallo + zero-fill", size=10),
           label_at=(480, 452))
    d.edge(clean, dirty, "b", "t", label=M("write", size=11))
    d.edge(clean, assigned, (0, 0.8), (1, 0.3), via=[(560, 191.2), (560, 299.2)],
           label=Line("expulsión (S=0)", size=10), label_at=(560, 250))
    d.edge(dirty, swapped, "r", (0.7, 1), via=[(932, 452)], label=Line("expulsión: swap-out", size=10),
           label_at=(880, 452))
    d.edge(swapped, clean, (0.3, 0), (1, 0.4), via=[(868, 165.6)], label=Line("read: swap-in", size=10),
           label_at=(830, 165))
    d.edge(clean, swapped, (1, 0.8), (0.1, 0), via=[(836, 191.2)], label=Line("expulsión (S=1)", size=10),
           label_at=(836, 240), dashed=True)
    d.edge(swapped, dirty, (0.1, 1), (1, 0.3), via=[(836, 439.2)], label=Line("write: swap-in", size=10),
           label_at=(836, 395), dashed=True)
    d.edge(assigned, none, (0.3, 1), "b", via=[(381, 380), (175, 380)],
           label=[M("free", size=11), Line("libera marco, swap y tabla vacía", size=10)], label_at=(260, 400))
    d.text(30, 450, 260, 80, [Line("free desde cualquier estado de la", size=10, color="#555555"),
                              Line("región vuelve a «No asignada».", size=10, color="#555555"),
                              Line("Una región liberada y reutilizada", size=10, color="#555555"),
                              Line("se entrega en cero.", size=10, color="#555555")], align="left")
    d.save(OUT)


if __name__ == "__main__":
    arquitectura()
    direccion()
    tabla_dos_niveles()
    flujo_traduccion()
    secuencia_fallo()
    clases()
    politicas()
    estados()
