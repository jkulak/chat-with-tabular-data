"""Functions for interacting with a language model using Vertex AI."""

import os

from dotenv import load_dotenv
from vertexai.language_models import TextGenerationModel


load_dotenv()

CANDIDATE_COUNT_LLM_PARAMETR = os.getenv("CANDIDATE_COUNT_LLM_PARAMETR")
MAX_OUTPUT_TOKENS_LLM_PARAMETR = os.getenv("MAX_OUTPUT_TOKENS_LLM_PARAMETR")
TEMPERATURE_LLM_PARAMETR = os.getenv("TEMPERATURE_LLM_PARAMETR")
TOP_P_LLM_PARAMETR = os.getenv("TOP_P_LLM_PARAMETR")
TOP_K_LLM_PARAMETR = os.getenv("TOP_K_LLM_PARAMETR")
VERTEX_AI_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
VERTEX_AI_LOCATION = os.getenv("GCP_PROJECT_ID")
LLM_RESOURCE_ID = os.getenv("LLM_RESOURCE_ID")


def prompt_llm(prompt: str) -> str:
    """Generate text based on the given prompt using a language model.

    Args:
    ----
        prompt (str): The text prompt to generate text from.

    Returns:
    -------
        str: The generated text.
    """
    parameters = {
        "candidate_count": int(CANDIDATE_COUNT_LLM_PARAMETR),
        "max_output_tokens": int(MAX_OUTPUT_TOKENS_LLM_PARAMETR),
        "temperature": float(TEMPERATURE_LLM_PARAMETR),
        "top_p": float(TOP_P_LLM_PARAMETR),
        "top_k": int(TOP_K_LLM_PARAMETR),
    }
    model = TextGenerationModel.from_pretrained(LLM_RESOURCE_ID)
    response = model.predict(prompt, **parameters)
    return response.text


def add_cap_ref(
    prompt: str,
    prompt_suffix: str,
    cap_ref: str,
    cap_ref_content: str,
) -> str:
    r"""Attache a capitalized reference to the prompt.

    Example:
    -------
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n
            return True'

    Returns:
    -------
        'Refactor this code. Make it more readable using this EXAMPLE.\n
        \n
        EXAMPLE\n
        \n
        def foo():\n
            return True'
    """
    return f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n{cap_ref_content}"""
