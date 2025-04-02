# Create flashcards automatically with AI.

We use uv to manage dependancy.

use the right version of python
```bash
uv python pin 3.13
```

Install:

```bash
uv add ipykernel ipython torch torchvision numpy matplotlib playwright langchain-core langchain-groq langchain beautifulsoup4 genanki pydub transformers nest_asyncio 

```

install firefox and chrome with playwright
```bash
uv run playwright install chrome firefox
```