import argparse
import json
import pathlib

import tqdm

from src import prepare_models
from src import create_workflow

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


def main(inputs: str, output: pathlib.Path):
    res = {}
    if output.exists():
        with open(output, "r", encoding="utf-8") as f:
            res = json.load(f)
    else:
        output.parent.mkdir(exist_ok=True, parents=True)

    llm = prepare_models()
    workflow = create_workflow(llm)
    graph = workflow.compile()
    sentences = prepare_sentences(inputs=inputs)
    print(f"There are {len(sentences)} sentences:")
    for sentence, val in tqdm.tqdm(sentences.items()):
        if sentence not in res:
            llm_output = graph.invoke({"arabic_sentence": sentence})["combined_output"]
            val["llm_output"] = llm_output
            res[sentence] = val
            with open(output, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=4)

    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Automatic translation of one sentence and output")
    parser.add_argument("--inputs", "--input", "-i", type=str, help="Sentence in Arabic")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="output")
    args = parser.parse_args()

    main(args.inputs, args.output)