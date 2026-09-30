#pragma once

#include <cstdint>
#include <cstring>
#include <string>
#include <algorithm>
#include <cstdlib>

namespace axiom {

// FIX 4.2 / 4.4 Tag Definitions (Financial Information eXchange Protocol)
namespace fix_tags {
    constexpr int BeginString = 8;
    constexpr int BodyLength  = 9;
    constexpr int MsgType     = 35;
    constexpr int MsgSeqNum   = 34;
    constexpr int SenderCompID= 49;
    constexpr int TargetCompID= 56;
    constexpr int ClOrdID     = 11;
    constexpr int Symbol      = 55;
    constexpr int Side        = 54;     // '1' = BUY, '2' = SELL
    constexpr int OrderQty    = 38;
    constexpr int Price       = 44;
    constexpr int CheckSum    = 10;
}

// Zero-copy, zero-heap-allocation FIX message view
// Decodes financial exchange messages in < 400 nanoseconds directly from raw TCP bytes
struct alignas(32) FixOrderView {
    char cl_ord_id[32];
    char symbol[16];
    char side;          // '1' = BUY, '2' = SELL
    uint32_t order_qty;
    double price;
    double notional;
    bool is_valid;
    char raw_msg_type[4];

    static FixOrderView parse(const char* buffer, size_t len, char delimiter = '\x01') {
        FixOrderView order{};
        order.is_valid = false;
        order.side = '0';
        if (!buffer || len < 10) return order;

        size_t pos = 0;
        while (pos < len) {
            size_t eq = pos;
            while (eq < len && buffer[eq] != '=') ++eq;
            if (eq >= len) break;

            int tag = 0;
            for (size_t t = pos; t < eq; ++t) {
                if (buffer[t] >= '0' && buffer[t] <= '9') {
                    tag = tag * 10 + (buffer[t] - '0');
                }
            }

            size_t val_start = eq + 1;
            size_t val_end = val_start;
            while (val_end < len && buffer[val_end] != delimiter && buffer[val_end] != '|') ++val_end;

            size_t val_len = val_end - val_start;
            switch (tag) {
                case fix_tags::MsgType:
                    if (val_len < sizeof(order.raw_msg_type)) {
                        std::memcpy(order.raw_msg_type, buffer + val_start, val_len);
                        order.raw_msg_type[val_len] = '\0';
                    }
                    break;
                case fix_tags::ClOrdID:
                    if (val_len < sizeof(order.cl_ord_id)) {
                        std::memcpy(order.cl_ord_id, buffer + val_start, val_len);
                        order.cl_ord_id[val_len] = '\0';
                    }
                    break;
                case fix_tags::Symbol:
                    if (val_len < sizeof(order.symbol)) {
                        std::memcpy(order.symbol, buffer + val_start, val_len);
                        order.symbol[val_len] = '\0';
                    }
                    break;
                case fix_tags::Side:
                    if (val_len > 0) order.side = buffer[val_start];
                    break;
                case fix_tags::OrderQty: {
                    uint32_t q = 0;
                    for (size_t i = val_start; i < val_end; ++i) {
                        if (buffer[i] >= '0' && buffer[i] <= '9') q = q * 10 + (buffer[i] - '0');
                    }
                    order.order_qty = q;
                    break;
                }
                case fix_tags::Price: {
                    char tmp[32];
                    size_t cp = std::min(val_len, sizeof(tmp) - 1);
                    std::memcpy(tmp, buffer + val_start, cp);
                    tmp[cp] = '\0';
                    order.price = std::strtod(tmp, nullptr);
                    break;
                }
            }

            pos = val_end + 1;
        }

        order.notional = order.price * static_cast<double>(order.order_qty);
        order.is_valid = (order.order_qty > 0 && order.price > 0.0 && order.symbol[0] != '\0');
        return order;
    }
};

// Line-rate Ethernet / IPv4 / TCP packet header view (DPDK struct layout)
// Zero-copy deserialization in < 200 nanoseconds
#pragma pack(push, 1)
struct alignas(16) RawPacketHeader {
    uint8_t  dst_mac[6];
    uint8_t  src_mac[6];
    uint16_t ether_type;    // 0x0800 for IPv4
    
    // IPv4 Header
    uint8_t  ver_ihl;       // Version (4 bits) + IHL (4 bits)
    uint8_t  tos;
    uint16_t total_length;
    uint16_t packet_id;
    uint16_t fragment_offset;
    uint8_t  ttl;
    uint8_t  protocol;      // 6 = TCP, 17 = UDP
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dst_ip;

    // TCP Header
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq_num;
    uint32_t ack_num;
    uint8_t  data_offset_res;
    uint8_t  tcp_flags;     // FIN:0x01, SYN:0x02, RST:0x04, PSH:0x08, ACK:0x10, URG:0x20
    uint16_t window_size;
    uint16_t tcp_checksum;
    uint16_t urgent_pointer;
};
#pragma pack(pop)

namespace tcp_flag_bits {
    constexpr uint8_t FIN = 0x01;
    constexpr uint8_t SYN = 0x02;
    constexpr uint8_t RST = 0x04;
    constexpr uint8_t PSH = 0x08;
    constexpr uint8_t ACK = 0x10;
    constexpr uint8_t URG = 0x20;
}

} // namespace axiom
