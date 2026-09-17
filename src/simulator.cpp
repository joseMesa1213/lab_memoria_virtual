#include "simulator.hpp"

#include <chrono>
#include <iomanip>
#include <sstream>

static std::string hex(std::uint64_t value, int width = 8) {
    std::ostringstream out;
    out << "0x" << std::hex << std::uppercase << std::setw(width) << std::setfill('0') << value;
    return out.str();
}

Simulator::Simulator(const Config& config, PolicyKind policy)
    : config_(config), manager_(config, policy) {}

RunSummary Simulator::run(const Trace& trace, std::ostream& log) {
    for (const TraceError& error : trace.errors) {
        log << "[L" << std::setw(4) << error.line << "] error de sintaxis: " << error.message << '\n';
    }
    const auto start = std::chrono::steady_clock::now();
    for (const Command& command : trace.commands) {
        execute(command, log);
    }
    manager_.statistics().totalTime = std::chrono::steady_clock::now() - start;

    RunSummary summary;
    summary.policy = manager_.policyName();
    summary.pageSize = manager_.layout().pageSize();
    summary.frames = manager_.frameCount();
    summary.stats = manager_.statistics();
    summary.liveTables = manager_.pageTable().liveTables();
    summary.createdTables = manager_.pageTable().createdTables();
    summary.swappedPages = manager_.swappedPages();
    summary.traceErrors = trace.errors.size();
    return summary;
}

void Simulator::execute(const Command& command, std::ostream& log) {
    const bool verbose = config_.verbose;
    const std::uint32_t address = static_cast<std::uint32_t>(command.first);
    switch (command.type) {
        case CommandType::Alloc: {
            std::optional<std::uint32_t> base = manager_.allocate(command.first);
            if (verbose || !base) {
                log << "[L" << std::setw(4) << command.line << "] alloc " << command.first << " -> ";
                if (base) {
                    log << "región en " << hex(*base) << '\n';
                } else {
                    log << "ERROR: espacio virtual insuficiente\n";
                }
            }
            break;
        }
        case CommandType::Free: {
            std::optional<std::uint64_t> length = manager_.release(address);
            if (verbose || !length) {
                log << "[L" << std::setw(4) << command.line << "] free " << hex(address) << " -> ";
                if (length) {
                    log << "liberados " << *length << " bytes\n";
                } else {
                    log << "ERROR: la dirección no es el inicio de una región asignada\n";
                }
            }
            break;
        }
        case CommandType::Read: {
            AccessResult result = manager_.read(address);
            if (verbose || result.status != AccessStatus::Ok) {
                logAccess(command, result, log);
            }
            break;
        }
        case CommandType::Write: {
            AccessResult result = manager_.write(address, static_cast<std::uint8_t>(command.second));
            if (verbose || result.status != AccessStatus::Ok) {
                logAccess(command, result, log);
            }
            break;
        }
    }
}

void Simulator::logAccess(const Command& command, const AccessResult& result, std::ostream& log) const {
    log << "[L" << std::setw(4) << command.line << "] " << std::left << std::setw(5)
        << commandName(command.type) << std::right << ' ' << hex(command.first);
    if (command.type == CommandType::Write) {
        log << " <- " << std::setw(3) << command.second;
    } else {
        log << "       ";
    }
    if (result.status == AccessStatus::SegmentationFault) {
        log << "  SEGFAULT: dirección no asignada\n";
        return;
    }
    log << "  (pt1=" << std::setw(4) << result.parts.pt1 << ", pt2=" << std::setw(4) << result.parts.pt2
        << ", off=" << hex(result.parts.offset, 3) << ") -> PA " << hex(result.physicalAddress)
        << "  marco " << std::setw(4) << result.frame;
    if (command.type == CommandType::Read) {
        log << "  valor=" << static_cast<unsigned>(result.value);
    }
    if (result.pageFault) {
        log << "  FALLO";
        if (result.swapIn) {
            log << " (swap-in)";
        }
        if (result.replacement) {
            log << " reemplazo vpn " << hex(result.evictedPage, 5)
                << (result.evictedDirty ? " (sucia->swap)" : " (limpia)");
        }
    } else {
        log << "  HIT";
    }
    log << '\n';
}

void printReport(const RunSummary& summary, std::ostream& out) {
    const Statistics& s = summary.stats;
    const double totalMs = std::chrono::duration<double, std::milli>(s.totalTime).count();
    const double faultMs = std::chrono::duration<double, std::milli>(s.faultTime).count();
    const double avgFaultNs =
        s.pageFaults == 0 ? 0.0 : static_cast<double>(s.faultTime.count()) / static_cast<double>(s.pageFaults);
    out << std::fixed << std::setprecision(2);
    out << "==================== Estadísticas finales ====================\n"
        << "Política: " << summary.policy << '\n'
        << "Tamaño de página: " << summary.pageSize << " bytes\n"
        << "Marcos físicos: " << summary.frames << " ("
        << static_cast<std::uint64_t>(summary.frames) * summary.pageSize / 1024 << " KB)\n"
        << "--------------------------------------------------------------\n"
        << "Total de accesos: " << s.accesses() << " (lecturas " << s.reads << ", escrituras " << s.writes
        << ")\n"
        << "Total fallos de página: " << s.pageFaults << '\n'
        << "Hit rate: " << s.hitRate() << "%\n"
        << "Total reemplazos: " << s.replacements << '\n'
        << "--------------------------------------------------------------\n"
        << "Páginas escritas a swap (swap-out): " << s.swapOuts << '\n'
        << "Páginas leídas de swap (swap-in): " << s.swapIns << '\n'
        << "Páginas inicializadas en cero: " << s.zeroFills << '\n'
        << "Accesos inválidos (segfault): " << s.segmentationFaults << '\n'
        << "Asignaciones: " << s.allocations << " (fallidas " << s.failedAllocations << ")\n"
        << "Liberaciones: " << s.releases << " (inválidas " << s.invalidReleases << ")\n"
        << "Tablas de nivel 2 creadas: " << summary.createdTables << " (vivas " << summary.liveTables << ")\n"
        << "Errores de sintaxis en la traza: " << summary.traceErrors << '\n'
        << "Tiempo total de simulación: " << totalMs << " ms\n"
        << "Tiempo en manejo de fallos: " << faultMs << " ms (promedio " << avgFaultNs << " ns/fallo)\n"
        << "==============================================================\n";
}

void printComparison(const std::vector<RunSummary>& summaries, std::ostream& out) {
    out << "\n======================== Comparación ========================\n"
        << std::left << std::setw(9) << "Política" << std::right << std::setw(10) << "Accesos" << std::setw(10)
        << "Fallos" << std::setw(11) << "Hit rate" << std::setw(12) << "Reemplazos" << std::setw(10)
        << "Swap-out" << '\n';
    out << std::fixed << std::setprecision(2);
    for (const RunSummary& summary : summaries) {
        const Statistics& s = summary.stats;
        out << std::left << std::setw(8) << summary.policy << std::right << std::setw(10) << s.accesses()
            << std::setw(10) << s.pageFaults << std::setw(10) << s.hitRate() << '%' << std::setw(12)
            << s.replacements << std::setw(10) << s.swapOuts << '\n';
    }
    out << "=============================================================\n";
}

void printCsvHeader(std::ostream& out) {
    out << "policy,page_size,frames,accesses,faults,hit_rate,replacements,swap_outs,swap_ins,segfaults,total_ms\n";
}

void printCsvRow(const RunSummary& summary, std::ostream& out) {
    const Statistics& s = summary.stats;
    out << std::fixed << std::setprecision(4) << summary.policy << ',' << summary.pageSize << ','
        << summary.frames << ',' << s.accesses() << ',' << s.pageFaults << ',' << s.hitRate() << ','
        << s.replacements << ',' << s.swapOuts << ',' << s.swapIns << ',' << s.segmentationFaults << ','
        << std::chrono::duration<double, std::milli>(s.totalTime).count() << '\n';
}
