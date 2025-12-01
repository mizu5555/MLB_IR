import json
from pathlib import Path


FIELD_CANONICAL_MAP = {
    "AVG": "batting_average",
    "OBP": "on_base_percentage",
    "SLG": "slugging_percentage",
    "OPS": "on_base_plus_slugging",
    "ISO": "isolated_power",
    "BABIP": "batting_average_on_balls_in_play",
    "HR": "home_runs",
    "RBI": "runs_batted_in",
    "BB%": "walk_rate",
    "K%": "strikeout_rate",
    "wRC+": "weighted_runs_created_plus",
    "wOBA": "weighted_on_base_average",
    "WAR": "wins_above_replacement",
    "ERA": "earned_run_average",
    "FIP": "fielding_independent_pitching",
    "xFIP": "expected_fielding_independent_pitching",
    "SIERA": "skill_interactive_era",
    "K/9": "strikeouts_per_9",
    "BB/9": "walks_per_9",
    "K/BB": "strikeout_walk_ratio",
    "WHIP": "walks_hits_per_inning_pitched",
    "HardHit%": "hard_hit_rate",
    "Barrel%": "barrel_rate",
}


def canonical_to_text(key: str) -> str:
    if key in FIELD_CANONICAL_MAP:
        return FIELD_CANONICAL_MAP[key].replace("_", " ")
    return key.replace("_", " ").lower()


def build_embedding_text(record):
    name = record["player_name"]
    season = record["season"]
    team = record["team"]
    ptype = record["type"]

    parts = [f"{name} {season} {ptype} for {team}."]

    for k, v in record["stats"].items():
        readable = canonical_to_text(k)
        parts.append(f"{readable} {v}.")

    return " ".join(parts)


def build_keyword_text(record):
    keys = [
        record["player_name"],
        str(record["season"]),
        record["team"],
        record["type"],
    ]

    for k, v in record["stats"].items():
        keys.append(str(k))
        keys.append(str(v))

    return " ".join(keys)


def build_field_text(record):
    return "\n".join([f"{k}: {v}" for k, v in record["stats"].items()])


def main():
    ROOT = Path(__file__).resolve().parents[2]
    input_file = ROOT / "data" / "mlb_data_adv" / "parsed_records.json"
    output_file = ROOT / "data" / "mlb_data_adv" / "training_data.json"

    print("📘 Loading parsed_records.json ...")
    with open(input_file, "r", encoding="utf-8") as f:
        parsed_records = json.load(f)

    training_data = []

    for rec in parsed_records:
        # ⭐ 建立唯一 id
        rec["id"] = f"{rec['player_name']}_{rec['player_id']}_{rec['season']}_{rec['type']}"

        # Build texts
        rec["embedding_text"] = build_embedding_text(rec)
        rec["keyword_text"] = build_keyword_text(rec)
        rec["field_text"] = build_field_text(rec)

        training_data.append(rec)

    print(f"💾 Saving training_data.json → {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)

    print("✅ Step1 Done!")


if __name__ == "__main__":
    main()
