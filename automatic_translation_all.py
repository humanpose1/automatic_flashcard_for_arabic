import argparse
import json
import pathlib
import time

import groq
from langchain_groq import ChatGroq
import tqdm

from src import prepare_qwen_models
from src import prepare_groq_model
from src import create_workflow
from src import QwenLLM

def prepare_sentences(inputs: str):
    with open(inputs, "r", encoding="utf-8") as f:
        data = json.load(f)
    input_per_sentence = {}
    for title, value in data.items():
        if "tashkeel" in value and "article" in value:
            if len(value["tashkeel"]) > 0 and len(value["tashkeel"]) == len(value["article"]):
                for sentence, sentence_tashkeel in zip(value["article"], value["tashkeel"]):
                    new_val = {
                        "arabic_sentence": sentence,
                        "true_tashkeel": sentence_tashkeel,
                        "title": title,
                        "link": value["link"],
                        "lang_break_content": value["lang_break_content"]
                    }
                    input_per_sentence[sentence] = new_val
    return input_per_sentence


def main(
        inputs: str,
        output: pathlib.Path,
        use_groq: bool):
    res = {}
    if output.exists():
        with open(output, "r", encoding="utf-8") as f:
            res = json.load(f)
    else:
        output.parent.mkdir(exist_ok=True, parents=True)

    llm: QwenLLM | ChatGroq
    if use_groq:
        llm = prepare_groq_model()
    else:
        llm = prepare_qwen_models()

    workflow = create_workflow(llm)
    graph = workflow.compile()
    sentences = prepare_sentences(inputs=inputs)
    print(f"There are {len(sentences)} sentences:")
    pbar = tqdm.tqdm(sentences.items())
    for sentence, val in pbar:
        if sentence not in res:
            start = time.time()
            has_error = True
            while has_error:
                try:
                    # Attempt to invoke the LLM
                    llm_output = graph.invoke({"arabic_sentence": sentence})["combined_output"]
                    # If successful, set has_error to False to exit the loop
                    has_error = False
                except (groq.APIConnectionError, groq.RateLimitError) as e:
                    # Handle the error (e.g., log it, wait before retrying, etc.)
                    has_error = True
                    print(f"An error occurred: {e}. Retrying in 60s...")
                    # Optionally, add a delay before retrying to avoid rapid consecutive attempts
                    time.sleep(60)
            
            end = time.time()
            pbar.set_description_str(f"time={end-start:2.1f}")
            val["llm_output"] = llm_output
            res[sentence] = val
            with open(output, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=4)

    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Automatic translation of one sentence and output")
    parser.add_argument("--inputs", "--input", "-i", type=str, help="Sentence in Arabic")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="output")
    parser.add_argument("--use-groq", action="store_true", help="Use Groq")
    args = parser.parse_args()

    main(args.inputs, args.output, args.use_groq)