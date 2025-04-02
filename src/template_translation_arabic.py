import functools
import json
import re

from langchain_core.language_models import BaseChatModel
from langgraph import graph
import markdown
import pydantic




class ArabicState(pydantic.BaseModel):
    arabic_sentence: str
    tashkeel_sentence: str = pydantic.Field(default=None, exclude=True)
    translated_sentence: str = pydantic.Field(default=None, exclude=True)
    vocabulary: str = pydantic.Field(default=None, exclude=True)
    explanation: str = pydantic.Field(default=None, exclude=True)
    combined_output: dict[str, str] = pydantic.Field(default=None, exclude=True)

def get_tashkeel(state: ArabicState, llm: BaseChatModel):
    query = f"""Get the 'tashkeel' (diacritical marks) of this arabic phrase, ensuring the meaning, tone, and syntax are preserved accurately.
    
    # Steps
    1. Comprehend the Arabic phrase and its nuances.
    2. Apply appropriate 'tashkeel' to the Arabic phrase considering grammar, pronunciation, and emphasis.
    3. Verify accuracy and make adjustments if needed.

    # Output
    Only respond with the fully tashkeel-marked Arabic phrase.

    # Example
    Input: بالنسبة إلى العديد من القرويين هنا يبدأ اليوم مع شروق الشمس
    Output: بِالنِّسْبَةِ إِلَى الْعَدِيدِ مِنَ الْقَرَوِيِّينَ هُنَا يَبْدَأُ الْيَوْمُ مَعَ شُرُوقِ الشَّمْسِ

    
    # Notes
    - Keep cultural and linguistic subtleties in mind.
    - Ensure pronunciation guides (tashkeel) are relevant to native Arabic speakers.


    Input: {state.arabic_sentence}
    Output:
    """
    msg = llm.invoke(query)
    return {"tashkeel_sentence": msg}

def get_translation(state: ArabicState, llm: BaseChatModel):
    query = f"""Translate the given Arabic text into English accurately.

    # Steps
    1. Read and understand the entire Arabic text carefully.
    2. Identify any phrases or expressions that may have cultural or contextual significance.
    3. Translate each part of the text to maintain the original meaning and intent.
    4. Ensure that the translated text is grammatically correct and flows naturally in English.

    # Output Format
    - Provide the translated English text in a clear and concise manner.

    # Examples
    Input: بِالنِّسْبَةِ إِلَى الْعَدِيدِ مِنَ الْقَرَوِيِّينَ هُنَا يَبْدَأُ الْيَوْمُ مَعَ شُرُوقِ الشَّمْسِ
    Output: For many villagers here, the day begins with sunrise.

    # Notes
    - Keep cultural and linguistic subtleties in mind.
    
    Input: {state.tashkeel_sentence}
    Output:
    """
    msg = llm.invoke(query)
    return {"translated_sentence": msg}

class WordAnalysis(pydantic.BaseModel):
    meanings: list[str] = pydantic.Field(description="List of meanings with the most relevant first")
    pronounciation: str = pydantic.Field(description="The pronunciation of the word")
    root: dict = pydantic.Field(description="Root word and its meaning if applicable")
    examples: list = pydantic.Field(description="List of example words with their meanings")
    singular_plural: dict = pydantic.Field(description="Singular and plural forms if the word is a noun")


def extract_json_from_markdown(markdown_text):
    # Regular expression to extract JSON inside triple backticks
    match = re.search(r"```json\n(.*?)\n```", markdown_text, re.DOTALL)
    
    if match:
        json_text = match.group(1)  # Extracted JSON string
        try:
            data = json.loads(json_text)  # Convert to dictionary
            return data
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return None
    else:
        print("No JSON found")
        return None

def get_word_by_word_analysis(state: ArabicState, llm: BaseChatModel):


    example_json =  """
    {
        "لقد": {
            "meanings": ["indeed", "certainly"],
            "pronounciation": "laqad",
            "root": {
            "root_word": "قد",
            "root_meaning": "to be able, to be certain"
            },
            "examples": [
            {"قد فعل": "he has done"},
            {"قد يكون": "he might be"}
            ],
            "singular/plural": {}
        },
        "كان": {
            "meanings": ["was", "used to be"],
            "pronounciation": "kāna",
            "root": {
            "root_word": "كون",
            "root_meaning": "to be, to exist"
            },
            "examples": [
            {"يكون": "he is"},
            {"كيان": "entity, being"}
            ],
            "singular/plural": {}
        },
        "جابر": {
            "meanings": ["Jabir (a name)", "one who mends or fixes"],
            "pronounciation": "Jābir",
            "root": {
            "root_word": "جبر",
            "root_meaning": "to mend, to force"
            },
            "examples": [
            {"جبر": "compulsion, coercion"},
            {"جبار": "tyrant, almighty"}
            ],
            "singular/plural": {
            "singular": "جابر",
            "plural": "جابِرون / جابِرين"
            }
        },
        "بن": {
            "meanings": ["son of"],
            "pronounciation": "bin",
            "root": {},
            "examples": [
            {"ابن سينا": "Ibn Sina (Avicenna)"},
            {"ابن رشد": "Ibn Rushd (Averroes)"}
            ],
            "singular/plural": {}
        },
        "حيان": {
            "meanings": ["Hayyan (a name)"],
            "pronounciation": "Ḥayyān",
            "root": {
            "root_word": "حي",
            "root_meaning": "to live"
            },
            "examples": [
            {"حياة": "life"},
            {"حي": "alive, neighborhood"}
            ],
            "singular/plural": {}
        },
        "عالما": {
            "meanings": ["a scholar", "a scientist"],
            "pronounciation": "ʿāliman",
            "root": {
            "root_word": "علم",
            "root_meaning": "knowledge, to know"
            },
            "examples": [
            {"عِلم": "science, knowledge"},
            {"عالم": "world, scholar"}
            ],
            "singular/plural": {
            "singular": "عالِم",
            "plural": "عُلَماء"
            }
        },
        "متعدد": {
            "meanings": ["multiple", "various"],
            "pronounciation": "mutaʿaddid",
            "root": {
            "root_word": "عدد",
            "root_meaning": "to count, number"
            },
            "examples": [
            {"عدد": "number"},
            {"تعداد": "enumeration"}
            ],
            "singular/plural": {
            "singular": "متعدد",
            "plural": "متعدِّدون / متعدِّدين"
            }
        },
        "التخصصات": {
            "meanings": ["specializations", "fields of expertise"],
            "pronounciation": "at-taḵaṣṣuṣāt",
            "root": {
            "root_word": "خصص",
            "root_meaning": "to specify, to specialize"
            },
            "examples": [
            {"تخصص": "specialization"},
            {"مُخَصَّص": "allocated, designated"}
            ],
            "singular/plural": {
            "singular": "تخصص",
            "plural": "التخصصات"
            }
        }
    }
    """

    query = f"""Provide a detailed word-by-word analysis for each word in the Arabic sentence to determine if it is a noun or a verb. For each word, include the following details: 
    1. Its multiple meanings (with the most relevant meaning listed first). 
    2. Its pronounciation 
    3. The root of the word along with its meaning if applicable. 
    4. Examples of other words that share the same root. 
    5. Singular and plural forms if the word is a noun.  

    # Output format 
    It must be in JSON format. Each word entry should follow this structure:
  - 'word1': {{'meanings': [meaning1, meaning2], 'pronounciation': 'pronouciation_value', 'root': {{'root_word': 'root_value', 'root_meaning': 'meaning_if_relevant'}}, 'examples': [{{'example_word': 'translation'}}, ...], 'singular/plural': {{'singular': 'word_singular', 'plural': 'word_plural'}} }},  


    # Example
    Input:  لقد كان جابر بن حيان عالما متعدد التخصصات
    Output: 
    ```json
    {example_json}
    ```

    Input: {state.tashkeel_sentence}
    Output:
    """

    
    msg = llm.invoke(query)
    vocab = extract_json_from_markdown(msg)
    if vocab is None:
        vocab = msg
    else:
        vocab = json.dumps(vocab, ensure_ascii=False, indent=4)
    return {"vocabulary": vocab}



def get_explanation(state: ArabicState, llm: BaseChatModel):
    
    
    query = f"""Analyze the following Arabic sentence:

    {state.tashkeel_sentence}

    Provide a detailed explanation including:

    1. Grammatical Breakdown:
    - Sentence structure
    - Key grammatical elements (e.g., verb forms, case endings, pronouns)
    - Explanation of any complex grammatical constructions

    2. Idiomatic Expressions:
    - Identify any idiomatic expressions in the sentence
    - Explain their meanings and usage

    3. Historical or Religious References:
    - Identify any historical or religious references in the sentence
    - Provide context and significance

    Format your response clearly, using headers for each section and bold for key terms.
    """

    msg = llm.invoke(query)
    return {"explanation": markdown.markdown(msg)}

def aggregate(state: ArabicState):
    combined_output = {}
    combined_output["arabic_sentence"] = state.arabic_sentence
    combined_output["tashkeel_sentence"] = state.tashkeel_sentence
    combined_output["translated_sentence"] = state.translated_sentence
    combined_output["vocabulary"] = state.vocabulary
    combined_output["explanation"] = state.explanation

    return {"combined_output": combined_output}
   
    
    



def create_workflow(llm: BaseChatModel):
    workflow = graph.StateGraph(ArabicState)

    # Create nodes
    workflow.add_node("get_tashkeel", functools.partial(get_tashkeel, llm=llm))
    workflow.add_node("get_translation", functools.partial(get_translation, llm=llm))
    workflow.add_node("get_word_by_word_analysis", functools.partial(get_word_by_word_analysis, llm=llm))
    workflow.add_node("get_explanation", functools.partial(get_explanation, llm=llm))
    workflow.add_node("aggregate", aggregate)

    # First edge to get tashkeel 
    workflow.add_edge(graph.START, "get_tashkeel")


    # Parallel processing to get translation, word by word analysis and explanation
    workflow.add_edge("get_tashkeel", "get_translation")
    workflow.add_edge("get_tashkeel", "get_word_by_word_analysis")
    workflow.add_edge("get_tashkeel", "get_explanation")


    # aggregate the results in a dict
    workflow.add_edge("get_translation", "aggregate")
    workflow.add_edge("get_word_by_word_analysis", "aggregate")
    workflow.add_edge("get_explanation", "aggregate")

    workflow.add_edge("aggregate", graph.END)
    return workflow




    

    