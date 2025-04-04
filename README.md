# Create flashcards automatically with AI.

We use uv to manage dependancy.

use the right version of python
```bash
uv venv --python 3.13
```

We installed everything like this:

```bash
uv add ipykernel ipython torch torchvision numpy matplotlib playwright langchain-core langchain-groq langchain beautifulsoup4 genanki pydub transformers nest_asyncio 
```

The `uv.lock` and `pyproject.toml` is here you can download as:
```bash
uv sync --locked
```

install firefox and chrome with playwright
```bash
uv run playwright install chrome firefox
```


We scrape media arabic sentence from [aljazeera learning platform](https://learning.aljazeera.net/en):
```bash
uv run python scrape_arabic_text.py -o out/article_all.json
```


Then to compute flashcard using llm you can use:

```bash
uv run python automatic_translation_all.py -i out/article_all.json -o out/article_all_with_llm.json
```

The model runs locally using QWen2.5 72B. If you want a faster model you can use Groq (by default it uses mistral-saba-24b)

You can find an diagram of the workflow to create the flashcard. It is a very simple workflow.
![Image](./graph.png)


```bash
uv run python automatic_translation_all.py -i out/article_all.json -o out/article_all_with_llm.json --use-groq
```

Do not forget to export
```bash
export GROQ_API_KEY=XXX
```



Then to create flashcard: use:
```bash
uv run python create_anki_flashcard.py -i out/articles_all_with_llm.json -o out/test.apkg --title FlashCard_Aljazeera_Learning
```