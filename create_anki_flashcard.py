import argparse
import json
import pathlib
import random
from typing import Optional, Sequence

import genanki
import tqdm


def json_to_html(json_str: str) -> str | None:
    try:
        data = json.loads(json_str)
        html = ""
        for word, details in data.items():
            html += f"<h2>{word}</h2>"
            html += f"<p><strong>Pronunciation:</strong> {details.get('pronounciation', 'N/A')}</p>"
            
            if 'meanings' in details:
                html += "<p><strong>Meanings:</strong> " + ", ".join(details['meanings']) + "</p>"
            
            if 'root' in details:
                root = details['root']
                html += f"<p><strong>Root Word:</strong> {root.get('root_word', 'N/A')}</p>"
                html += f"<p><strong>Root Meaning:</strong> {root.get('root_meaning', 'N/A')}</p>"
            
            if 'examples' in details and details['examples']:
                html += "<p><strong>Examples:</strong></p><ul>"
                for example in details['examples']:
                    for phrase, meaning in example.items():
                        html += f"<li><strong>{phrase}:</strong> {meaning}</li>"
                html += "</ul>"
            
            html += "<hr>"
    except json.JSONDecodeError as e:
        print(f"Cannot Parse JSON {e}")
        html = None
    return html


def get_random_number() -> int:
    return random.randrange(1 << 30, 1 << 31)

def get_parser():
    parser = argparse.ArgumentParser("Create flashcard based on a json")
    parser.add_argument("--input-json", "-i", type=pathlib.Path)
    parser.add_argument("--title", type=str)
    parser.add_argument("--out", "-o", type=pathlib.Path)
    parser.add_argument("--labels", type=str, nargs="+", default=None)
    return parser

class FlashCard:

    def __init__(self, model: genanki.Model, deck: genanki.Deck) -> None:
        self.model = model
        self.deck = deck
    
    def add_reversible_flashcard(
            self,
            info: dict[str, str | dict],
            labels: Optional[Sequence[str]]=None) -> genanki.Deck:
        llm_output = info["llm_output"]
        vocab = json_to_html(llm_output["vocabulary"])
        if vocab is not None:
            note = genanki.Note(
                model=self.model,
                fields=[
                    info["arabic_sentence"],
                    info["true_tashkeel"],
                    llm_output["translated_sentence"],
                    vocab,
                    llm_output["explanation"],
                    info["link"],
                ]
            )
            if labels is not None:
                note.tags.extend(labels)
            self.deck.add_note(note)

def init_flashcard_reverse(title: str) -> FlashCard:

    arabic_html = '''
        <div id="arabic">{{Arabic}}</div>
        <div id="hidden-tashkeel">
            <p class="trigger" onclick="toggleMessage('tashkeel')">[Tashkeel]</p>
            <p id="tashkeel" class="hidden">{{Tashkeel}}</p>
        </div>
        <div id="link">
            Link: <a href={{Link}}>{{Link}}</a>
        </div>

        <script>
            function toggleMessage(uid) {
                var message = document.getElementById(uid);
                message.classList.toggle('hidden');
            }
        </script>
        <style>
            .hidden {
                display: none;
            }
            .trigger {
                cursor: pointer;
                color: blue;
                text-decoration: underline;
            }
        </style>
    '''

    english_html = '''
        <div id="english">{{English}}</div>

        <div id="hidden-vocabulary">
            <p class="trigger" onclick="toggleMessageEn('vocabulary')">[Vocabulary]</p>
            <div id="vocabulary" class="hidden">{{Vocabulary}}</div>
        </div>

        <div id="hidden-explanation">
            <p class="trigger" onclick="toggleMessageEn('explanation')">[Explanation]</p>
            <div id="explanation" class="hidden">{{Explanation}}</div>
        </div>

        <div id="link">
            Link: <a href="{{Link}}">{{Link}}</a>
        </div>

        <script>
            function toggleMessageEn(uid) {
                var message = document.getElementById(uid);
                if (message) {
                    message.classList.toggle('hidden'); // Toggle visibility
                } else {
                    console.error("Element with ID '" + uid + "' not found!");
                }
            }
        </script>

        <style>
            .hidden {
                display: none;
            }
            .trigger {
                cursor: pointer;
                color: blue;
                text-decoration: underline;
            }
        </style>
    '''

    model = genanki.Model(
        get_random_number(),
        'Reversible Cards',
        fields=[
            {'name': 'Arabic'},
            {'name': 'Tashkeel'},
            {'name': "English"},
            {'name': "Vocabulary"},
            {'name': "Explanation"},
             {'name': "Link"}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': arabic_html,
                'afmt': english_html
            },
            {
                'name': 'Card 2',
                'qfmt': english_html,
                'afmt': arabic_html,
            },
    ])
    deck = genanki.Deck(
        get_random_number(),
        title)
    return FlashCard(model, deck)

def main(input_json: pathlib.Path, title: str, out: pathlib.Path):
    flashcard = init_flashcard_reverse(title)
    with open(input_json, "r", encoding='utf-8') as f:
        data: dict = json.load(f)
    for info in tqdm.tqdm(data.values()):
        flashcard.add_reversible_flashcard(info)
    genanki.Package(flashcard.deck).write_to_file(out)


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.input_json, args.title, args.out)

    
    