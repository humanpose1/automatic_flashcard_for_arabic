from typing import List, Optional


from langchain.llms.base import LLM
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
import transformers

def prepare_models(model_name: str = "Qwen/Qwen2.5-72B-Instruct-AWQ"):
    

    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)

    llm = QwenLLM(model=model, tokenizer=tokenizer)
    return llm


def prepare_groq_model(model_name: str = "mistral-saba-24b"):
    llm = ChatGroq(
        model=model_name,
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    
    )
    




def execute_prompt(
        prompt: str,
        model: transformers.AutoModelForCausalLM,
        tokenizer: transformers.AutoTokenizer):
    messages = [
        {"role": "system", "content": "You are a helpful assistant, expert in arabic and english language."},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=8192
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response

class QwenLLM(LLM, BaseModel):
    model: transformers.Qwen2ForCausalLM 
    tokenizer: transformers.Qwen2TokenizerFast

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return execute_prompt(prompt, self.model, self.tokenizer)