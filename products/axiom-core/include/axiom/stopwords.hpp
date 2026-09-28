#pragma once

#include <string>
#include <unordered_set>
#include <vector>
#include <cctype>

namespace axiom {

inline bool is_stopword(const std::string& word) {
    static const std::unordered_set<std::string> k_stopwords = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an",
        "and", "any", "are", "as", "at", "be", "because", "been", "before",
        "being", "below", "between", "both", "but", "by", "can", "cannot",
        "could", "did", "do", "does", "doing", "down", "during", "each",
        "few", "for", "from", "further", "had", "has", "have", "having",
        "he", "her", "here", "hers", "herself", "him", "himself", "his",
        "how", "i", "if", "in", "into", "is", "it", "its", "itself",
        "just", "me", "more", "most", "my", "myself", "no", "nor", "not",
        "now", "of", "off", "on", "once", "only", "or", "other", "our",
        "ours", "ourselves", "out", "over", "own", "please", "same", "should",
        "so", "some", "such", "than", "that", "the", "their", "theirs",
        "them", "themselves", "then", "there", "these", "they", "this",
        "those", "through", "to", "too", "under", "until", "up", "very",
        "was", "we", "were", "what", "when", "where", "which", "while",
        "who", "whom", "why", "will", "with", "would", "you", "your",
        "yours", "yourself", "yourselves"
    };
    return k_stopwords.find(word) != k_stopwords.end();
}

// Tokenizes text into lowercase alphanumeric words, filtering stopwords if non-stopwords exist
inline std::vector<std::string> extract_meaningful_tokens(const std::string& text) {
    std::vector<std::string> all_words;
    std::string current;
    for (size_t i = 0; i <= text.size(); ++i) {
        char c = (i < text.size()) ? static_cast<char>(std::tolower(text[i])) : ' ';
        if (std::isalnum(static_cast<unsigned char>(c))) {
            current += c;
        } else if (!current.empty()) {
            all_words.push_back(current);
            current.clear();
        }
    }

    std::vector<std::string> filtered;
    filtered.reserve(all_words.size());
    for (const auto& w : all_words) {
        if (!is_stopword(w)) {
            filtered.push_back(w);
        }
    }

    // If query only consisted of stopwords (e.g. "what is this"), retain all words
    if (filtered.empty()) {
        return all_words;
    }
    return filtered;
}

} // namespace axiom
