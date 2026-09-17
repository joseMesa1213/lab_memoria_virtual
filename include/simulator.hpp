#pragma once

#include "config.hpp"
#include "memory_manager.hpp"
#include "trace.hpp"

#include <ostream>
#include <string>
#include <vector>

struct RunSummary {
    std::string policy;
    std::uint32_t pageSize = 0;
    std::uint32_t frames = 0;
    Statistics stats;
    std::size_t liveTables = 0;
    std::size_t createdTables = 0;
    std::size_t swappedPages = 0;
    std::size_t traceErrors = 0;
};

class Simulator {
public:
    Simulator(const Config& config, PolicyKind policy);

    RunSummary run(const Trace& trace, std::ostream& log);

private:
    void execute(const Command& command, std::ostream& log);
    void logAccess(const Command& command, const AccessResult& result, std::ostream& log) const;

    Config config_;
    MemoryManager manager_;
};

void printReport(const RunSummary& summary, std::ostream& out);
void printComparison(const std::vector<RunSummary>& summaries, std::ostream& out);
void printCsvHeader(std::ostream& out);
void printCsvRow(const RunSummary& summary, std::ostream& out);
