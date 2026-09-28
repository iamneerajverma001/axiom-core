#include "axiom/engine.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <cassert>
#include <cmath>

using namespace axiom;

void test_empty_string(AxiomEngine& engine) {
    std::cout << "[Test 1] Empty String Input: ";
    DecisionResult res = engine.decide("");
    std::cout << "Path=" << (int)res.path 
              << ", Conf=" << res.choice.confidence 
              << ", Entropy=" << res.shannon_entropy 
              << ", Latency=" << res.latency_total_us << "us" << std::endl;
    if (std::isnan(res.choice.confidence) || std::isnan(res.shannon_entropy)) {
        std::cout << "  --> FAILED: NaN detected in confidence or entropy!" << std::endl;
    } else {
        std::cout << "  --> Passed." << std::endl;
    }
}

void test_massive_string(AxiomEngine& engine) {
    std::cout << "[Test 2] Massive 100,000-char Payload: ";
    std::string massive(100000, 'X');
    DecisionResult res = engine.decide(massive);
    std::cout << "Path=" << (int)res.path 
              << ", Conf=" << res.choice.confidence 
              << ", Latency=" << res.latency_total_us << "us" << std::endl;
    if (std::isnan(res.choice.confidence)) {
        std::cout << "  --> FAILED: NaN detected!" << std::endl;
    } else {
        std::cout << "  --> Passed." << std::endl;
    }
}

void test_unicode_special_chars(AxiomEngine& engine) {
    std::cout << "[Test 3] Unicode / Emojis / Malformed Bytes: ";
    std::string unicode_str = "\xF0\x9F\x94\xA5\xE2\x9A\xA1\x00\xFF\xFE\xFD Alert! \0 hidden null";
    DecisionResult res = engine.decide(unicode_str);
    std::cout << "Path=" << (int)res.path 
              << ", Conf=" << res.choice.confidence << std::endl;
    std::cout << "  --> Passed." << std::endl;
}

void test_schema_edge_cases() {
    std::cout << "[Test 4] Empty Schema (0 sectors): ";
    AxiomEngine engine(DeviceType::DIRECTML_GPU, 128, 0.01f);
    SchemaDefinition empty_schema;
    engine.load_schema(empty_schema);
    DecisionResult res = engine.decide("Hello world");
    std::cout << "Path=" << (int)res.path << ", ChoiceID=" << res.choice.choice_id << std::endl;
    
    std::cout << "[Test 5] Single-Leaf Schema (1 sector, 1 leaf): ";
    SchemaDefinition single_schema;
    SectorDefinition sec;
    sec.sector_id = 0;
    sec.name = "Solo_Sector";
    sec.leaves = {{999, "Solo_Leaf", "Only option"}};
    single_schema.sectors = {sec};
    engine.load_schema(single_schema);
    DecisionResult res2 = engine.decide("Anything");
    std::cout << "Path=" << (int)res2.path << ", Conf=" << res2.choice.confidence 
              << ", Entropy=" << res2.shannon_entropy << std::endl;
}

void test_massive_leaf_scaling() {
    std::cout << "[Test 6] 500-Leaf Stress Test (Scaling Limits): ";
    AxiomEngine engine(DeviceType::DIRECTML_GPU, 128, 0.01f);
    SchemaDefinition big_schema;
    for (int s = 0; s < 10; ++s) {
        SectorDefinition sec;
        sec.sector_id = s;
        sec.name = "Sector_" + std::to_string(s);
        for (int l = 0; l < 50; ++l) {
            sec.leaves.push_back({static_cast<uint32_t>(s * 100 + l), "Leaf_" + std::to_string(s) + "_" + std::to_string(l), "Desc"});
        }
        big_schema.sectors.push_back(sec);
    }
    engine.load_schema(big_schema);
    DecisionResult res = engine.decide("Test query for scaling");
    std::cout << "Path=" << (int)res.path 
              << ", Selected=" << res.choice.label 
              << ", Conf=" << res.choice.confidence 
              << ", Latency=" << res.latency_total_us << "us" << std::endl;
}

int main() {
    std::cout << "================================================================" << std::endl;
    std::cout << "       AXIOM-1 CHIEF TESTER DEEP SYSTEM AUDIT SUITE             " << std::endl;
    std::cout << "================================================================" << std::endl;

    SchemaDefinition schema;
    schema.confidence_threshold = 0.85f;
    schema.entropy_threshold = 0.20f;
    SectorDefinition sec;
    sec.sector_id = 0;
    sec.name = "Billing";
    sec.leaves = {{1, "Refund", "Money back"}, {2, "Tax", "Invoice"}};
    schema.sectors = {sec};

    AxiomEngine engine(DeviceType::DIRECTML_GPU, 64, 0.01f);
    engine.load_schema(schema);

    test_empty_string(engine);
    test_massive_string(engine);
    test_unicode_special_chars(engine);
    test_schema_edge_cases();
    test_massive_leaf_scaling();

    std::cout << "================================================================" << std::endl;
    std::cout << "Audit execution finished." << std::endl;
    return 0;
}
