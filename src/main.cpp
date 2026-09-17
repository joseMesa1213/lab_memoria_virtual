#include "config.hpp"
#include "simulator.hpp"
#include "trace.hpp"

#include <exception>
#include <iostream>
#include <sstream>
#include <vector>

int main(int argc, char** argv) {
    Config config;
    try {
        config = parseArguments(argc, argv);
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << "\n\n";
        printUsage(argv[0]);
        return 2;
    }
    if (config.help) {
        printUsage(argv[0]);
        return 0;
    }

    try {
        const Trace trace = loadTrace(config.inputPath);
        std::vector<RunSummary> summaries;
        if (config.csv) {
            printCsvHeader(std::cout);
        }
        for (PolicyKind policy : config.policies) {
            Simulator simulator(config, policy);
            std::ostringstream discarded;
            std::ostream& log = config.csv ? static_cast<std::ostream&>(discarded) : std::cout;
            RunSummary summary = simulator.run(trace, log);
            if (config.csv) {
                printCsvRow(summary, std::cout);
            } else {
                printReport(summary, std::cout);
            }
            summaries.push_back(summary);
        }
        if (!config.csv && summaries.size() > 1) {
            printComparison(summaries, std::cout);
        }
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
