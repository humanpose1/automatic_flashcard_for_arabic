"""Here we use groq with langchain. We will try a complex prompting system."""
import argparse
import json
import pathlib
import time

from src import prepare_models
from src import create_workflow


def main(sentence: str, output: pathlib.Path):
    
    llm = prepare_models()
    workflow = create_workflow(llm)
    graph = workflow.compile()
    start = time.time()
    res = graph.invoke({"arabic_sentence": sentence})["combined_output"]
    end = time.time()
    print(res)
    print(f"It took: {end - start: 2.2f}s")
    output.parent.mkdir(exist_ok=True, parents=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Automatic translation of one sentence and output")
    parser.add_argument("--sentence", type=str, help="Sentence in Arabic")
    parser.add_argument("--output", "-o", type=pathlib.Path, help="output")
    args = parser.parse_args()

    main(args.sentence, args.output)


    