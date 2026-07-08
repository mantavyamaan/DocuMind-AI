import json
from rag import ask_base_model, ask_rag_model


EVAL_FILE = "eval/questions.json"


def contains_expected_answer(answer: str, expected: str) -> bool:
    answer_lower = answer.lower()
    expected_keywords = expected.lower().split()

    matched_keywords = 0

    for word in expected_keywords:
        if len(word) > 3 and word in answer_lower:
            matched_keywords += 1

    return matched_keywords >= max(2, len(expected_keywords) // 3)


def evaluate():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Metrics
    factual_total = 0
    hallucination_test_total = 0
    
    base_factual_correct = 0
    rag_factual_correct = 0
    
    base_hallucinations = 0
    rag_hallucinations = 0
    
    rag_source_citations = 0

    results = []

    for item in questions:
        question = item["question"]
        expected = item["expected_answer"]
        is_hallucination_test = item["source"] == "none"

        print(f"\nQuestion: {question}")

        base_answer = ask_base_model(question)
        
        # Evaluate RAG model without streaming to get pure text output
        from rag import stream_rag_model
        rag_stream_result = stream_rag_model(question)
        rag_answer = "".join([chunk for chunk in rag_stream_result["answer_stream"]])
        rag_sources = rag_stream_result["sources"]

        base_match = contains_expected_answer(base_answer, expected)
        
        # For hallucination tests, we want to see if the model safely refused
        if is_hallucination_test:
            hallucination_test_total += 1
            # If base model did NOT say it couldn't find it (which it won't because it guesses), it's a hallucination
            refusal_keywords = ["could not find", "not available", "not mention"]
            base_refused = any(k in base_answer.lower() for k in refusal_keywords)
            rag_refused = any(k in rag_answer.lower() for k in refusal_keywords)
            
            if not base_refused:
                base_hallucinations += 1
            if not rag_refused:
                rag_hallucinations += 1
                
        else:
            factual_total += 1
            rag_match = contains_expected_answer(rag_answer, expected)
            if base_match:
                base_factual_correct += 1
            if rag_match:
                rag_factual_correct += 1
                
            # Check source grounding for valid questions
            if len(rag_sources) > 0 and rag_sources[0] != "Unknown":
                rag_source_citations += 1

        results.append({
            "question": question,
            "expected": expected,
            "is_hallucination_test": is_hallucination_test,
            "base_answer": base_answer,
            "rag_answer": rag_answer,
            "sources": rag_sources
        })

    # Compile Final Metrics
    matrix = {
        "Factual_Accuracy": {
            "Base": f"{base_factual_correct / factual_total * 100:.1f}%" if factual_total else "0%",
            "RAG": f"{rag_factual_correct / factual_total * 100:.1f}%" if factual_total else "0%"
        },
        "Hallucination_Rate": {
            "Base": f"{base_hallucinations / hallucination_test_total * 100:.1f}%" if hallucination_test_total else "0%",
            "RAG": f"{rag_hallucinations / hallucination_test_total * 100:.1f}%" if hallucination_test_total else "0%"
        },
        "Source_Grounding": {
            "Base": "0.0%",
            "RAG": f"{rag_source_citations / factual_total * 100:.1f}%" if factual_total else "0%"
        }
    }

    print("\n" + "="*40)
    print("EVALUATION MATRIX SUMMARY")
    print("="*40)
    print(f"Total Factual Questions: {factual_total}")
    print(f"Total Hallucination Tests: {hallucination_test_total}\n")
    
    for metric, scores in matrix.items():
        print(f"--- {metric.replace('_', ' ')} ---")
        print(f"Base Model: {scores['Base']}")
        print(f"RAG Model:  {scores['RAG']}\n")

    output_data = {
        "matrix": matrix,
        "details": results
    }

    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)


if __name__ == "__main__":
    evaluate()
