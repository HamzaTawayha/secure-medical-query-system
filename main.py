from app_logic import run_secure_query


def main():
    result = run_secure_query(
        age_min=30,
        diagnosis="epilepsy",
        outcome=None,
        keyword="hippocampus"
    )

    print("Query Input:")
    print(result["query_input"])
    print()

    print("Risk Score:", result["risk_score"])
    print("Risk Probability:", result["risk_probability"])
    print("Decision:", result["decision"])
    print("Review Priority:", result["review_priority"])
    print("Decision Reason:", result["decision_reason"])
    print("Log ID:", result["log_id"])
    print()

    print("Patients:")
    for patient in result["patients"]:
        print(patient)

    print()

    print("Notes:")
    for note in result["notes"]:
        print(note)


if __name__ == "__main__":
    main()
