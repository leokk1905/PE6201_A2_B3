import json

auto_result_path = "d4_scripted_56_trials.json"
human_review_path = "d4_human_review_edited.json"

with open(auto_result_path, "r", encoding="utf-8") as f:
    auto_data = json.load(f)
with open(human_review_path, "r", encoding="utf-8") as f:
    human_data = json.load(f)

# 人工评审：case_id -> passed
human_dict = {}
for entry in human_data:
    cid = entry["case_id"]
    human_dict[cid] = entry["passed"]

# 自动结果：去重，每个case_id拿第一条trial的passed
auto_case_dict = {}
for trial in auto_data:
    cid = trial["case_id"]
    if cid not in auto_case_dict:
        auto_case_dict[cid] = trial["passed"]

match_count = 0
total_checked = len(human_dict)

print(f"{'case_id':<8} {'auto_passed':<12} {'human_passed':<12} {'match?'}")
print("-" * 45)

for cid in human_dict.keys():
    auto_p = auto_case_dict[cid]
    human_p = human_dict[cid]
    matched = (auto_p == human_p)
    if matched:
        match_count += 1
    print(f"{cid:<8} {str(auto_p):<12} {str(human_p):<12} {matched}")

print("-" * 45)
print(f"Total manually reviewed cases: {total_checked}")
print(f"Matches: {match_count}")
print(f"Mismatches: {total_checked - match_count}")
consistency = 100.0 * match_count / total_checked
print(f"Consistency: {consistency:.1f} %")
