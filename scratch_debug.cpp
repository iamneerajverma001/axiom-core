#include "axiom/engine.hpp"
#include <iostream>

using namespace axiom;

SchemaDefinition create_robust_schema() {
    SchemaDefinition schema;
    schema.schema_id = "schema_enterprise_triage_v2";
    schema.domain = "Enterprise Operations & Risk Routing";
    schema.confidence_threshold = 0.70f;
    schema.entropy_threshold = 0.40f;
    schema.conformal_alpha = 0.01f;

    SectorDefinition sec_billing;
    sec_billing.sector_id = 0;
    sec_billing.name = "Sector_Billing_Finance";
    sec_billing.leaves = {
        {101, "Refund_Dispute", "refund dispute chargeback money back refund payment unauthorized charge cancel charge refund request"},
        {102, "Invoice_Tax_Exemption", "VAT corporate tax certificate invoice receipt tax exemption billing document"},
        {103, "Subscription_Cancellation", "cancel subscription downgrade churn cancel plan terminate account cancel membership"},
        {104, "Payment_Method_Failure", "credit card declined payment failed gateway error billing card error transaction failure"}
    };

    SectorDefinition sec_security;
    sec_security.sector_id = 1;
    sec_security.name = "Sector_Security_Auth";
    sec_security.leaves = {
        {201, "Credential_Stuffing_Alert", "compromised account login burst brute force attack credential stuffing ip alert"},
        {202, "MFA_Token_Reset", "reset 2fa authentication reset mfa token lost phone lost 2fa hardware key two factor reset"},
        {203, "Privilege_Escalation_Attempt", "unauthorized iam role change privilege escalation root access exploit security breach"},
        {204, "API_Key_Exfiltration", "exposed secret public repository api key leaked secret token stolen credential"}
    };

    SectorDefinition sec_infra;
    sec_infra.sector_id = 2;
    sec_infra.name = "Sector_Cloud_Infrastructure";
    sec_infra.leaves = {
        {301, "K8s_Pod_CrashLoop", "kubernetes pod crashloop oomkilled container memorypressure cluster failure k8s restart"},
        {302, "Database_Deadlock_Spike", "postgresql database deadlock lock contention query timeout db pool exhaustion"},
        {303, "Network_Egress_Anomaly", "bandwidth egress spike directconnect network traffic threshold abnormal egress"},
        {304, "Storage_IOPS_Saturation", "ebs volume disk latency iops saturation storage degradation drive full"}
    };

    schema.sectors = {sec_billing, sec_security, sec_infra};
    return schema;
}

int main() {
    HierarchicalRegisterTree tree;
    SchemaDefinition schema = create_robust_schema();
    tree.compile_schema(schema);

    SparseTensorLoop loop;
    loop.initialize();

    std::vector<std::string> test_queries = {
        "reset my 2fa authentication",
        "Immediate refund dispute on unauthorized charge #9401",
        "Reset MFA token lost phone authenticate user",
        "Kubernetes worker node OOMKilled crashloop alert",
        "hello delete to day downloaded file",
        "Write a 3-line python function to calculate Fibonacci numbers"
    };

    ArenaPool pool(16);

    for (const auto& q : test_queries) {
        MemoryFrame& frame = pool.acquire();
        float emb[64];
        loop.forward_sparse(q, frame, emb, 64);
        Layer2Evaluation eval = tree.evaluate(emb, 64, frame);

        std::cout << "----------------------------------------" << std::endl;
        std::cout << "Query: " << q << std::endl;
        std::cout << "Path : " << (eval.fast_path_eligible ? "FAST_PATH (<1ms)" : "SYSTEM2_FALLBACK (Qwen)") << std::endl;
        std::cout << "Leaf : " << eval.selected_leaf_name << " (ID: " << eval.selected_leaf_id << ")" << std::endl;
        std::cout << "Prob : " << eval.max_probability << " | Entr: " << eval.shannon_entropy << std::endl;
    }

    return 0;
}
