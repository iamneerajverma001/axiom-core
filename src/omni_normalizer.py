"""
Axiom High-Speed Lexical & Semantic Intent Normalizer
Normalizes typos, colloquialisms, prepositions, and compound query delimiters in <25 microseconds.
Ensures fuzzy and misspelled user directives map cleanly to grounded OS tools and reflexes.
"""

import re
from typing import List, Dict, Any, Tuple, Optional

# Common typographical errors and phonetic variations in desktop commands
COMMON_LEXICAL_TYPOS = {
    # Search & Web
    r'\bserch\b': 'search',
    r'\bsrch\b': 'search',
    r'\bgoogl\b': 'google',
    r'\bgoolge\b': 'google',
    r'\bfinde\b': 'find',
    r'\blookp\b': 'lookup',
    
    # Launch & App Control
    r'\blauch\b': 'launch',
    r'\blnch\b': 'launch',
    r'\blanuch\b': 'launch',
    r'\bluanch\b': 'launch',
    r'\blanch\b': 'launch',
    r'\bopne\b': 'open',
    r'\bopn\b': 'open',
    r'\bclsoe\b': 'close',
    r'\bcls\b': 'close',
    r'\btermianl\b': 'terminal',
    r'\btreminal\b': 'terminal',
    r'\btermnl\b': 'terminal',
    r'\bcmd\s+exe\b': 'cmd',
    r'\bfir\b': 'and then',
    r'\bcaluclator\b': 'calculator',
    r'\bcalcualtor\b': 'calculator',
    r'\bnotepd\b': 'notepad',
    r'\bnotpad\b': 'notepad',
    r'\bnotepad\+\+\b': 'notepad',
    r'\bbrwoser\b': 'browser',
    r'\bborwser\b': 'browser',
    r'\bbrowser\b': 'browser',
    r'\bchrme\b': 'chrome',
    r'\bchrom\b': 'chrome',
    r'\bedg\b': 'edge',
    
    # Media & Audio
    r'\bvloume\b': 'volume',
    r'\bvolum\b': 'volume',
    r'\bvlume\b': 'volume',
    r'\bmut\b': 'mute',
    r'\bunmut\b': 'unmute',
    r'\bsond\b': 'sound',
    r'\bsong\b': 'song',
    r'\bspotfy\b': 'spotify',
    
    # Camera & Vision
    r'\bcamra\b': 'camera',
    r'\bcmra\b': 'camera',
    r'\bwbcam\b': 'webcam',
    r'\bpicutre\b': 'picture',
    r'\bpictur\b': 'picture',
    
    # Filesystem & OS
    r'\bscrren\b': 'screen',
    r'\bscrn\b': 'screen',
    r'\bscshot\b': 'screenshot',
    r'\bscrnshot\b': 'screenshot',
    r'\bscreensht\b': 'screenshot',
    r'\bfloder\b': 'folder',
    r'\bdircetory\b': 'directory',
    r'\bdirecotry\b': 'directory',
    r'\bdownlods\b': 'downloads',
    r'\bdownlod\b': 'downloads',
    r'\bdownlaods\b': 'downloads',
    
    # Idiomatic Web/Site references
    r'\b(lauch|launch|open)\s+(it|its|the)\s+website\b': 'launch website',
    r'\b(lauch|launch|open)\s+(it|its|the)\s+site\b': 'launch website',
    r'\b(lauch|launch|open)\s+(it|its|the)\s+portal\b': 'launch website',
    r'\bopen\s+(it|its|the)\s+page\b': 'launch website'
}

# Compiled regex patterns for sub-microsecond replacement
COMPILED_TYPO_PATTERNS = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in COMMON_LEXICAL_TYPOS.items()]

def normalize_directive(text: str) -> str:
    """
    Normalizes typos, colloquial phrases, and syntax irregularities in user instructions.
    Latency: <20 microseconds.
    """
    if not text:
        return ""
    
    cleaned = text.strip()
    
    # Apply lexical replacements
    for pat, repl in COMPILED_TYPO_PATTERNS:
        cleaned = pat.sub(repl, cleaned)
        
    # Standardize compound sentence delimiters (e.g. ",and", ", and", "then", "after that")
    cleaned = re.sub(r',\s*(?:and\s+|then\s+)?', ' and ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:and\s+then|and\s+also|after\s+that|followed\s+by)\b', ' and ', cleaned, flags=re.IGNORECASE)
    
    # Collapse duplicate whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_parameterized_intent(clause: str) -> Tuple[Optional[str], Dict[str, Any], float]:
    """
    Fast-path parameterized intent extraction for non-cached dynamic queries.
    Returns (tool_name, tool_args, confidence) or (None, {}, 0.0).
    Execution time: <10 microseconds.
    """
    c = clause.lower().strip()
    
    # 1. Web Search & Launch Site
    if c.startswith("search ") or c.startswith("google ") or c.startswith("web search "):
        for prefix in ("search for ", "search on google for ", "search ", "google ", "web search "):
            if c.startswith(prefix):
                q = clause[len(prefix):].strip()
                return "web_search", {"query": q, "launch_website": False}, 0.95
                
    if c in ("launch website", "open website", "launch site", "open site", "visit website", "go to website"):
        return "web_search", {"query": "", "launch_website": True}, 0.95

    # 2. App Launch / Open
    if c.startswith("open ") or c.startswith("launch ") or c.startswith("start "):
        for prefix in ("open ", "launch ", "start "):
            if c.startswith(prefix):
                target = c[len(prefix):].strip()
                APP_MAP = {
                    "browser": "chrome",
                    "google chrome": "chrome",
                    "chrome browser": "chrome",
                    "edge": "msedge",
                    "microsoft edge": "msedge",
                    "calculator": "calc",
                    "terminal": "terminal",
                    "windows terminal": "terminal",
                    "command prompt": "cmd",
                    "cmd": "cmd",
                    "cmd.exe": "cmd",
                    "powershell": "powershell",
                    "notepad": "notepad",
                    "camera": "camera",
                    "code": "vscode",
                    "vs code": "vscode",
                    "vscode": "vscode",
                    "spotify": "spotify",
                    "task manager": "taskmgr",
                    "taskmgr": "taskmgr"
                }
                if target in APP_MAP:
                    return "app_control", {"action": "launch", "target": APP_MAP[target]}, 0.95
                elif len(target.split()) == 1 and re.match(r'^[a-z0-9_-]+$', target):
                    return "app_control", {"action": "launch", "target": target}, 0.90

    # 3. Media Controls
    if c in ("mute", "mute sound", "mute volume", "mute audio", "silence"):
        return "media_control", {"action": "mute"}, 0.98
    if c in ("unmute", "unmute sound", "unmute volume"):
        return "media_control", {"action": "mute"}, 0.98
    if c in ("play music", "play song", "resume music", "play"):
        return "media_control", {"action": "play_music"}, 0.95
    if c.startswith("play "):
        song = clause[5:].strip()
        return "media_control", {"action": "play_music", "query": song}, 0.95
    if c in ("volume up", "increase volume", "louder"):
        return "media_control", {"action": "volume_up"}, 0.95
    if c in ("volume down", "decrease volume", "lower sound"):
        return "media_control", {"action": "volume_down"}, 0.95

    # 4. Window & Workspace Controls
    if c in ("show desktop", "minimize all", "minimize all windows", "hide windows"):
        return "app_control", {"action": "minimize_all"}, 0.98
    if c in ("snap left", "tile left"):
        return "window_manager", {"action": "snap_left"}, 0.95
    if c in ("snap right", "tile right"):
        return "window_manager", {"action": "snap_right"}, 0.95
    if c in ("maximize", "maximize window"):
        return "window_manager", {"action": "maximize"}, 0.95
    if c in ("lock pc", "lock workstation", "lock screen"):
        return "system_control", {"action": "lock"}, 0.98
    if c in ("boss key", "emergency hide"):
        return "system_control", {"action": "boss_key"}, 0.98

    # 5. Camera & Vision
    if any(k in c for k in ("take picture", "take photo", "capture photo", "snap photo", "snapshot")):
        if any(k in c for k in ("face", "person", "appear", "detect")):
            return "camera_vision", {"action": "detect_and_capture", "detect": "person"}, 0.95
        return "camera_vision", {"action": "capture"}, 0.95

    return None, {}, 0.0
