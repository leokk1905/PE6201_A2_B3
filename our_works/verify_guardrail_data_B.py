#!/usr/bin/env python3
"""
Verify that guardrail test data exists in data_B
"""
import json
import os

def verify_guardrail_data():
    """Verify all guardrail test cases exist in data_B"""

    print("="*70)
    print("GUARDRAIL TEST DATA VERIFICATION (data_B only)")
    print("="*70)
    print()

    # Data location
    data_b_path = os.path.join("A2_reference_data", "A2_reference_data", "data_B")
    print(f"Data location: {data_b_path}")
    print()

    # Expected guardrail case IDs
    expected_refs = [
        "REF-GR01",           # Step cap
        "REF-GR02",           # Budget ceiling
        "REF-GR03",           # Duplicate detection
        "REF-GR04-SUGGEST",   # Autonomy gate - suggest
        "REF-GR04-CONFIRM",   # Autonomy gate - confirm
        "REF-GR04-ACT",       # Autonomy gate - act
        "REF-GR08-HOSTILE",   # Hostile text - system override
        "REF-GR09-HOSTILE",   # Hostile text - loop induction
        "REF-GR10-HOSTILE",   # Hostile text - token explosion
        "REF-GR11-PARALLEL",  # Parallel duplicates
        "REF-GR12-CUMULATIVE" # Cumulative budget
    ]

    expected_patients = [
        "P-GR01", "P-GR02", "P-GR03",
        "P-GR04A", "P-GR04B", "P-GR04C",
        "P-GR08", "P-GR09", "P-GR10",
        "P-GR11", "P-GR12"
    ]

    # Load data files
    refs_path = os.path.join(data_b_path, "referrals.json")
    patients_path = os.path.join(data_b_path, "patients.json")
    contacts_path = os.path.join(data_b_path, "contacts.json")

    with open(refs_path) as f:
        referrals = json.load(f)
    with open(patients_path) as f:
        patients = json.load(f)
    with open(contacts_path) as f:
        contacts = json.load(f)

    # Extract IDs
    ref_ids = [r["referral_id"] for r in referrals]
    patient_ids = [p["patient_id"] for p in patients]
    contact_ids = [c["patient_id"] for c in contacts]

    # Check referrals
    print("REFERRALS:")
    print("-" * 70)
    found_refs = [rid for rid in expected_refs if rid in ref_ids]
    missing_refs = [rid for rid in expected_refs if rid not in ref_ids]

    print(f"Expected: {len(expected_refs)}")
    print(f"Found:    {len(found_refs)}")
    print()

    if missing_refs:
        print("MISSING:")
        for rid in missing_refs:
            print(f"  - {rid}")
    else:
        print("[OK] All referral test cases present")
    print()

    # Show details
    print("Details:")
    for rid in found_refs:
        ref = next(r for r in referrals if r["referral_id"] == rid)
        summary = ref["clinical_summary"][:60] + "..." if len(ref["clinical_summary"]) > 60 else ref["clinical_summary"]
        print(f"  {rid:20s} {ref['specialty']:4s} - {summary}")
    print()

    # Check patients
    print("PATIENTS:")
    print("-" * 70)
    found_patients = [pid for pid in expected_patients if pid in patient_ids]
    missing_patients = [pid for pid in expected_patients if pid not in patient_ids]

    print(f"Expected: {len(expected_patients)}")
    print(f"Found:    {len(found_patients)}")
    print()

    if missing_patients:
        print("MISSING:")
        for pid in missing_patients:
            print(f"  - {pid}")
    else:
        print("[OK] All patient test records present")
    print()

    # Check contacts
    print("CONTACTS:")
    print("-" * 70)
    found_contacts = [pid for pid in expected_patients if pid in contact_ids]
    missing_contacts = [pid for pid in expected_patients if pid not in contact_ids]

    print(f"Expected: {len(expected_patients)}")
    print(f"Found:    {len(found_contacts)}")
    print()

    if missing_contacts:
        print("MISSING:")
        for pid in missing_contacts:
            print(f"  - {pid}")
    else:
        print("[OK] All contact test records present")
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    all_good = (
        len(missing_refs) == 0 and
        len(missing_patients) == 0 and
        len(missing_contacts) == 0
    )

    if all_good:
        print("[SUCCESS] All guardrail test data is present in data_B")
        print()
        print(f"  {len(found_refs)} referral test cases")
        print(f"  {len(found_patients)} patient records")
        print(f"  {len(found_contacts)} contact records")
        print()
        print("Guardrail categories covered:")
        print("  - Step cap (turn limits)")
        print("  - Budget ceiling (token limits)")
        print("  - Duplicate action prevention")
        print("  - Autonomy gate (suggest/confirm/act)")
        print("  - Hostile text injection (3 cases)")
        print()
        print("Documentation:")
        doc_path = os.path.join("A2_reference_data", "A2_reference_data", "GUARDRAIL_TEST_CASES.md")
        if os.path.exists(doc_path):
            print(f"  [OK] {doc_path}")
        else:
            print(f"  [MISSING] {doc_path}")
        print()
        return 0
    else:
        print("[FAILED] Some guardrail test data is missing")
        print()
        if missing_refs:
            print(f"  Missing {len(missing_refs)} referrals")
        if missing_patients:
            print(f"  Missing {len(missing_patients)} patients")
        if missing_contacts:
            print(f"  Missing {len(missing_contacts)} contacts")
        print()
        return 1

if __name__ == "__main__":
    try:
        exit_code = verify_guardrail_data()
        exit(exit_code)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
