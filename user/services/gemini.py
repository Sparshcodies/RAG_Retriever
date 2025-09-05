import re
import json
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

embedding_model = "models/embedding-001"
chat_model = "gemini-2.0-flash"

def embed_text(text: str) -> list[float]:
    resp = genai.embed_content(model=embedding_model, content=text)
    return resp["embedding"]

def generate_grounded_answer(query: str, snippets: list):
    snippet_lines = []
    for i, s in enumerate(snippets, start=1):
        snippet_lines.append(f"[{i}] {s.get('text_excerpt','')}\n(source: {s.get('title') or s.get('source')}, pos:{s.get('position')})")
    snippets_str = "\n\n".join(snippet_lines)
    system = (
        "You are a grounded answer generator. Use ONLY the provided snippets to answer. "
        "Cite snippets inline using bracketed numbers like [1], [2]. "
        "If the snippets do not contain the answer, reply exactly: 'I could not find an answer in the provided sources.'"
    )
    prompt = f"{system}\n\nSnippets:\n{snippets_str}\n\nUser question: {query}\n\nAnswer (concise, include inline citations):"
    model = genai.GenerativeModel(chat_model)
    resp = model.generate_content(prompt)
    return resp.text

def verify_answer_is_grounded(answer_text: str, snippets: list):
    snippet_list = "\n".join([f"[{i+1}] {s.get('text_excerpt','')}" for i,s in enumerate(snippets)])
    verify_prompt = (
        "You are an assistant that checks grounding. Here are the snippets:\n"
        f"{snippet_list}\n\n"
        f"Here is the generated answer:\n{answer_text}\n\n"
        "For each sentence in the answer, say whether it is fully supported by one or more snippets. "
        "Answer in JSON with keys: {supported: bool, unsupported_sentences: [..]}. "
        "If all supported, output {\"supported\": true, \"unsupported_sentences\": []}."
    )
    model = genai.GenerativeModel(chat_model)
    resp = model.generate_content(verify_prompt)
    try:
        json_text = re.search(r'\{.*\}', resp.text, flags=re.S).group(0)
        return json.loads(json_text)
    except Exception:
        return {"supported": False, "unsupported_sentences": ["verification_failed"]}