import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List


# ============================================================
# Utility: 欄位名稱標準化
# ============================================================

def normalize_key(key: str) -> str:
    key = key.strip()

    KEY_MAP = {
        "Batting Average": "AVG",
        "On-Base Percentage": "OBP",
        "Slugging Percentage": "SLG",
        "On-Base Plus Slugging": "OPS",
        "Home Runs": "HR",
        "Runs Batted In": "RBI",
        "Walk Rate": "BB%",
        "Strikeout Rate": "K%",
        "Barrel Rate": "Barrel%",
        "Hard-Hit Rate": "HardHit%",
    }

    if key in KEY_MAP:
        return KEY_MAP[key]

    return key.replace(" ", "_")


# ============================================================
# Utility: value 轉型
# ============================================================

def parse_value(value: str) -> Any:
    value = value.strip()

    if value.endswith("%"):
        try:
            return float(value.replace("%", ""))
        except:
            return value

    if re.match(r"^-?\d+(\.\d+)?$", value):
        return float(value) if "." in value else int(value)

    if value.startswith("$"):
        try:
            return float(value.replace("$", ""))
        except:
            return value

    if "(" in value and ")" in value:
        cleaned = value.replace("(", "").replace(")", "").replace("$", "")
        try:
            return -float(cleaned)
        except:
            return value

    return value


# ============================================================
# 解析 stats 區段
# ============================================================

def parse_stats_block(block: str) -> Dict[str, Any]:
    stats = {}
    parts = block.split(";")

    for part in parts:
        part = part.strip()
        if not part or ":" not in part:
            continue

        key, value = part.split(":", 1)
        key = normalize_key(key)
        value = parse_value(value)
        stats[key] = value

    return stats


# ============================================================
# 解析單筆 key = "Name_ID_Season"
# ============================================================

def parse_single_entry(key: str, raw_text: str) -> List[Dict[str, Any]]:
    """
    例：
        "Shohei Ohtani_19755_2022"
    raw_text:
        "Season: 2022; ... ||| Type: pitcher; ..."
    """
    name, pid, season = key.split("_")
    season = int(season)

    segments = raw_text.split("|||")
    records = []

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        type_match = re.search(r"Type:\s*(\w+)", seg)
        team_match = re.search(r"Team:\s*(\w+)", seg)

        player_type = type_match.group(1).lower() if type_match else "unknown"
        team = team_match.group(1) if team_match else "UNK"

        stats = parse_stats_block(seg)
        record_key = f"{name}_{pid}_{season}_{player_type}"

        records.append({
            "record_key": record_key,
            "player_name": name,
            "player_id": pid,
            "season": season,
            "team": team,
            "type": player_type,
            "raw_text": seg,
            "clean_text": seg.replace(";", ". "),
            "stats": stats
        })

    return records


# ============================================================
# 執行主程式：text_chunks.json → parsed_records / player_db
# ============================================================

def main():
    ROOT = Path(__file__).resolve().parents[2]
    input_path = ROOT / "data" / "mlb_data_adv" / "text_chunks.json"
    out_parsed = ROOT / "data" / "mlb_data_adv" / "parsed_records.json"
    out_player_db = ROOT / "data" / "mlb_data_adv" / "player_db.json"

    print(f"Loading {input_path} ...")
    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    all_records = []
    player_db = {}

    for key, raw in chunks.items():
        entry_records = parse_single_entry(key, raw)
        all_records.extend(entry_records)

        name, pid, season = key.split("_")
        season = int(season)

        pid_key = f"{name}_{pid}"

        if pid_key not in player_db:
            player_db[pid_key] = {
                "name": name,
                "id": pid,
                "seasons": {}  # <-- 用 dict 儲存每季的 player_type list
            }

        if season not in player_db[pid_key]["seasons"]:
            player_db[pid_key]["seasons"][season] = set()

        for rec in entry_records:
            player_db[pid_key]["seasons"][season].add(rec["type"])

    # 將 set 轉回 list
    for pid_key in player_db:
        for season in player_db[pid_key]["seasons"]:
            player_db[pid_key]["seasons"][season] = list(player_db[pid_key]["seasons"][season])

    # 輸出
    print(f"Saving parsed → {out_parsed}")
    with open(out_parsed, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print(f"Saving player_db → {out_player_db}")
    with open(out_player_db, "w", encoding="utf-8") as f:
        json.dump(player_db, f, indent=2, ensure_ascii=False)

    print("Step0 Done ✓")


if __name__ == "__main__":
    main()
