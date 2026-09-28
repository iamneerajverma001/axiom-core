#include "axiom/engine.hpp"
#include <iostream>
#include <iomanip>

using namespace axiom;

SchemaDefinition create_unified_pc_engineering_schema() {
    SchemaDefinition schema;
    schema.schema_id = "schema_axiom_enterprise_v2";
    schema.domain = "Axiom-1 Universal Autonomous Decision & Engineering Engine";
    schema.confidence_threshold = 0.70f;
    schema.entropy_threshold = 0.40f;
    schema.conformal_alpha = 0.05f;

    SectorDefinition sec_os; sec_os.sector_id = 0; sec_os.name = "Sector_OS_Hardware";
    sec_os.leaves = {
        {401, "Process_Kill_Hog", "kill frozen process terminate task stop lagging app end process kill process task manager kill task assassin terminate process"},
        {402, "Port_Free_Liberate", "free port kill port port in use address already in use kill port 3000 free port 8000 liberate port port listener release port"},
        {403, "Disk_Clean_Temp", "clean temp files purge cache clean build cache cleanup disk space clean temporary files purge temporary scratch space clear cache"},
        {404, "Power_EcoQoS_Toggle", "battery saver mode eco mode silent fan efficiency mode cool laptop zero fan study mode power plan ecoqos"},
        {405, "Workstation_Lock_Sleep", "lock pc lock workstation put laptop to sleep sleep pc lock screen sleep workstation lock my workstation"},
        {406, "Audio_Mute_Volume", "volume control mute microphone mute speakers switch audio device headphone volume audio slider"},
        {407, "Display_Brightness_Res", "adjust screen brightness night light display resolution refresh rate monitor dim screen"},
        {408, "Bluetooth_Device_Cycle", "reconnect bluetooth headphones reset bluetooth radio adapter bluetooth toggle pair wireless mouse"},
        {409, "Clipboard_History_Wipe", "clear windows clipboard buffer sanitize sensitive text history purge clipboard paste buffer"},
        {410, "System_Telemetry_Snapshot", "cpu ram gpu temperature utilization hardware sensors report diagnostics hardware probe"}
    };

    SectorDefinition sec_dev; sec_dev.sector_id = 1; sec_dev.name = "Sector_Dev_Terminal";
    sec_dev.leaves = {
        {501, "Git_Quick_Sync", "git commit push git sync save code to github git auto stage push repository git status commit changes"},
        {502, "Compiler_Diag_Fix", "compiler error fix build failed g++ clang template error compilation fix syntax error build crash linker error"},
        {503, "Terminal_Error_Fix", "terminal error command failed self healing terminal fix command exit code error stderr fix shell"},
        {504, "Docker_Service_Control", "restart docker stop containers prune docker restart redis restart postgres container status docker compose"},
        {505, "Package_Env_Resolve", "python pip venv npm yarn poetry dependency conflict resolve lockfile mismatch package manager"},
        {506, "Code_Format_Lint", "prettier black ruff clang-format auto format codebase lint style guide indent code beautify"},
        {507, "Test_Runner_Coverage", "run pytest jest cargo test benchmark test suite code coverage unit tests integration tests"},
        {508, "Git_Branch_Rebase", "git checkout branch merge rebase conflict cherry pick resolve merge conflict git stash"},
        {509, "Gdb_Debugger_Trace", "core dump stack trace attach gdb lldb breakpoint inspection memory segfault debug trace"},
        {510, "Cmake_Build_Config", "cmake ninja configure rebuild targets toolchain generator compile flags cpack build matrix"}
    };

    SectorDefinition sec_research; sec_research.sector_id = 2; sec_research.name = "Sector_Research_Memory";
    sec_research.leaves = {
        {601, "Paper_Arxiv_Capture", "arxiv paper research paper read paper summary pdf extract novelty literature review academic paper"},
        {602, "Code_Snippet_Recall", "find code snippet search python script search regex search function code recall search local file symbol graph"},
        {603, "Equation_OCR_Extract", "ocr equation latex formula extract math from screen lecture slide equation mathpix derivation"},
        {604, "Idea_Log_Append", "log research idea save note quick idea note task logger research log log thought breakthrough insight note"},
        {605, "Citation_Bibtex_Gen", "generate bibtex reference citation doi scholarly paper cite paper bibliography export"},
        {606, "Literature_Survey_Map", "related work survey state of the art taxonomy comparative table research landscape gap analysis"},
        {607, "Dataset_Schema_Inspect", "parquet csv jsonl dataset schema summary statistics head data profiling column distributions"},
        {608, "Notebook_Cell_Execute", "jupyter notebook headless cell execution export html markdown ipynb run script data science"},
        {609, "Concept_Graph_Link", "associate concepts obsidian zettelkasten markdown link graph knowledge graph second brain backlink"},
        {610, "Benchmark_Plot_Export", "matplotlib seaborn latency throughput chart export svg generate evaluation graph chart"}
    };

    SectorDefinition sec_database; sec_database.sector_id = 3; sec_database.name = "Sector_Database_Storage";
    sec_database.leaves = {
        {301, "Postgres_Deadlock_Kill", "postgresql deadlock transaction lock timeout kill deadlocked pid pg_stat_activity query lock contention"},
        {302, "Redis_Cache_Flush", "redis flush keys cache eviction memory policy redis-cli monitor redis key pattern purge"},
        {303, "Migration_Rollback_Apply", "alembic flyway prisma database schema migration apply rollback revert migration db up down"},
        {304, "Connection_Pool_Tune", "pgbouncer hikari connection pool exhaustion max connections pool size timeout tune queue"},
        {305, "Slow_Query_Explain", "sql explain analyze query optimization index scan sequential scan high cost slow query tune"},
        {306, "Database_Backup_Dump", "pg_dump mysqldump s3 backup archive compressed database snapshot backup restore dump"},
        {307, "Elastic_Index_Reindex", "elasticsearch opensearch index mapping shard rebalance refresh index reindex documents"},
        {308, "SQLite_WAL_Checkpoint", "sqlite pragma wal_checkpoint vacuum analyze database optimize sqlite fragmentation checkpoint"},
        {309, "Storage_IOPS_Saturation", "disk volume iops latency degraded queue depth saturation disk bottleneck ebs nvme throttle"},
        {310, "Vector_DB_Index_Build", "faiss qdrant milvus hnsw vector index build compact nearest neighbor embedding database index"}
    };

    SectorDefinition sec_security; sec_security.sector_id = 4; sec_security.name = "Sector_Network_Security";
    sec_security.leaves = {
        {201, "Firewall_Rule_Add", "windows firewall ufw iptables allow block inbound outbound port firewall rule security group"},
        {202, "MFA_Token_Reset", "reset 2fa authentication hardware token authenticator key lost phone two factor reset reset authentication"},
        {203, "SSL_Cert_Inspect", "check tls certificate expiry date openssl handshake verify chain certbot renew ssl cert"},
        {204, "DNS_Latency_Probe", "dig nslookup flushdns resolve domain latency packet loss dns cache lookup query time"},
        {205, "Credential_Stuffing_Alert", "brute force login spike rate limit ban ip fail2ban credential stuffing auth attack burst"},
        {206, "IAM_Privilege_Audit", "audit aws iam role permissions privilege escalation token policy audit unauthorized access"},
        {207, "API_Key_Exfiltration", "revoke leaked exposed secret public github repo rotate token compromise secret leak key"},
        {208, "VPN_Tunnel_Reconnect", "wireguard openvpn tailscale zerotier tunnel reconnect route vpn gateway drop connection"},
        {209, "Packet_Sniffer_Trace", "wireshark tcpdump capture packet network interface dropped syn flood network packet trace"},
        {210, "SSH_Key_Distribute", "ssh-copy-id generate ed25519 key authorized_keys agent public key authentication ssh connect"}
    };

    SectorDefinition sec_window; sec_window.sector_id = 5; sec_window.name = "Sector_Window_Workspace";
    sec_window.leaves = {
        {701, "Window_Snap_Tile", "snap window snap left snap right tile grid split screen split window snap window to side maximize window"},
        {702, "Window_Minimize_All", "minimize all windows show desktop reveal desktop hide all windows clear screen desktop view"},
        {703, "Virtual_Desktop_Switch", "switch virtual desktop next desktop previous desktop switch workspace new desktop virtual workspace"},
        {704, "Focus_Mode_Isolate", "focus mode isolate active window aero shake minimize background apps distraction free coding mode"},
        {705, "Multi_Monitor_Move", "move window to next monitor secondary screen display switch window move display dual monitor"},
        {706, "Window_Find_Activate", "find window activate application bring to front switch to chrome switch to vscode switch to terminal focus app"},
        {707, "Window_Pin_Topmost", "pin window on top always on top toggle topmost keep on top float window stay on top"},
        {708, "Window_Screenshot_Crop", "take screenshot screen snip capture window snip tool screenshot active window screen clip"},
        {709, "Private_Windows_Hide", "boss key hide private windows quick hide panic button hide browser mute and hide private screen"},
        {710, "Workspace_Layout_Restore", "restore workspace layout arrange windows coding layout multi monitor setup split workspace layout"}
    };

    SectorDefinition sec_media; sec_media.sector_id = 6; sec_media.name = "Sector_Media_Display_Audio";
    sec_media.leaves = {
        {801, "Audio_Output_Switch", "switch audio device switch to headphones switch to speakers toggle audio playback output device sound endpoint"},
        {802, "Microphone_Privacy_Mute", "mute microphone mic mute toggle mic privacy hardware mic mute silence microphone uncheck mic"},
        {803, "Volume_Master_Adjust", "volume control increase volume lower volume mute sound volume slider sound level sound mixer"},
        {804, "Display_Night_Light", "night light blue light filter eye comfort warm screen color temperature night mode display night"},
        {805, "Media_Playback_Control", "play music pause music next track previous track media play pause media key playback control spotify play"},
        {806, "Screen_Recording_Trigger", "start screen recording stop recording capture video record desktop xbox game bar obs record"},
        {807, "Webcam_Privacy_Guard", "webcam privacy disable webcam camera killswitch turn off webcam camera privacy guard"},
        {808, "Display_Orientation_Rotate", "rotate screen display orientation portrait mode landscape mode rotate monitor screen flip"},
        {809, "Color_Profile_HDR", "toggle hdr windows hdr vibrant color profile high dynamic range display color settings"},
        {810, "Ambient_Brightness_Sync", "auto brightness adjust brightness dim screen brighten display ambient light sync screen brightness"}
    };

    SectorDefinition sec_automation; sec_automation.sector_id = 7; sec_automation.name = "Sector_Automation_File_System";
    sec_automation.leaves = {
        {901, "Duplicate_File_Sweep", "find duplicate files scan duplicate large files waste disk space duplicate cleaner deduplicate storage"},
        {902, "Downloads_Auto_Organize", "organize downloads folder sort downloads clean downloads folder categorize downloads files organize messy downloads"},
        {903, "Bulk_File_Rename", "bulk rename batch rename files rename pattern timestamp prefix renamer mass rename files"},
        {904, "Archive_Extract_Compress", "extract zip file unzip archive decompress tar gz compress folder create zip file rar extract"},
        {905, "Symlink_Folder_Create", "create symlink directory junction mklink folder shortcut link directory symbolic link"},
        {906, "Registry_Stale_Sweep", "clean registry stale mru sweep windows registry temp registry keys scan registry optimize registry"},
        {907, "Startup_Apps_Audit", "audit startup apps check startup programs disable slow startup boot speed up windows startup list"},
        {908, "Windows_Service_Bounce", "restart windows service service status stop service background service bounce restart spooler"},
        {909, "File_Hash_Integrity", "compute file hash sha256 checksum verify download integrity md5 hash file signature verify"},
        {910, "Project_Auto_Backup", "backup project create workspace backup zip snapshot auto backup project folder archive snapshot"}
    };

    schema.sectors = {sec_os, sec_dev, sec_research, sec_database, sec_security, sec_window, sec_media, sec_automation};
    return schema;
}

int main() {
    auto hash_word = [](const std::string& w, size_t dim) {
        uint64_t h1 = 0xcbf29ce484222325ULL;
        uint64_t h2 = 0x100000001b3ULL;
        for (char ch : w) {
            h1 = (h1 ^ static_cast<unsigned char>(ch)) * 0x100000001b3ULL;
            h2 = (h2 + static_cast<unsigned char>(ch)) * 0xcbf29ce484222325ULL;
        }
        size_t idx1 = h1 % dim;
        size_t idx2 = (h2 ^ (h1 >> 16)) % dim;
        std::cout << "Word '" << w << "' -> idx1=" << idx1 << ", idx2=" << idx2 << std::endl;
    };

    std::cout << "=== Query words (dim=256) ===" << std::endl;
    hash_word("play", 256);
    hash_word("music", 256);
    hash_word("youtube", 256);

    std::cout << "=== Duplicate_File_Sweep words (dim=256) ===" << std::endl;
    hash_word("duplicate", 256);
    hash_word("files", 256);
    hash_word("scan", 256);
    hash_word("large", 256);
    hash_word("waste", 256);
    hash_word("disk", 256);
    hash_word("space", 256);

    std::cout << "=== Media_Playback_Control words (dim=256) ===" << std::endl;
    hash_word("play", 256);
    hash_word("music", 256);
    hash_word("youtube", 256);
    hash_word("song", 256);
    hash_word("media", 256);
    hash_word("playback", 256);

    return 0;
}
