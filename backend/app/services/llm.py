from __future__ import annotations

import logging

from google import genai
from google.genai import types

from app.services.rag import RetrievedChunk


logger = logging.getLogger("ai-akash")

SYSTEM_PROMPT = """You are AI Akash, the portfolio assistant for Akash Tomy.
Answer as Akash would: confident, concise, practical, and recruiter-friendly.
Only answer using the provided context. If the answer is not in the context, say:
"I don't have that information - reach out to Akash directly."
Do not invent project names, employers, dates, metrics, links, or credentials.
Answer naturally. If retrieved context uses "Q:" and "A:" labels, do not repeat those labels.
Keep answers under 150 words unless the user asks for detail."""

RETRY_SUFFIX = "The previous draft ended abruptly. Answer the question again with a complete final sentence."


class LlmService:
  def __init__(self, api_key: str | None, fallback_api_key: str | None, model: str) -> None:
    self.model = model
    keys = [key for key in [api_key, fallback_api_key] if key]
    self.clients = [genai.Client(api_key=key) for key in dict.fromkeys(keys)]

  def answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
    if not self.clients:
      return _offline_answer(chunks)

    context = "\n\n".join(
      f"Source: {chunk.source} | Topic: {chunk.topic}\n{_clean_context_text(chunk.text)}"
      for chunk in chunks
    )

    for client_index, client in enumerate(self.clients, start=1):
      try:
        answer = self._generate(client, question, context)
        if _looks_incomplete(answer):
          logger.warning("Gemini chat client %s returned an incomplete answer; retrying once.", client_index)
          answer = self._generate(client, question, context, retry=True)
        if _looks_incomplete(answer):
          logger.warning("Gemini chat client %s returned another incomplete answer; using offline answer.", client_index)
          return _offline_answer(chunks)
        return answer
      except Exception as exc:
        logger.warning("Gemini chat client %s failed. error=%s", client_index, exc)

    logger.warning("All Gemini chat clients failed; using offline answer.")
    return _offline_answer(chunks)

  def _generate(self, client, question: str, context: str, retry: bool = False) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}"
    if retry:
      prompt = f"{prompt}\n\n{RETRY_SUFFIX}"

    response = client.models.generate_content(
      model=self.model,
      contents=prompt,
      config=types.GenerateContentConfig(
        max_output_tokens=360,
        temperature=0.4,
      ),
    )
    return response.text.strip()


def _offline_answer(chunks: list[RetrievedChunk]) -> str:
  if not chunks:
    return "I don't have that information - reach out to Akash directly."
  return _clean_context_text(chunks[0].text)


def _clean_context_text(text: str) -> str:
  if text.startswith("Q: ") and " A: " in text:
    return text.split(" A: ", 1)[1]
  return text


def _looks_incomplete(text: str) -> bool:
  stripped = text.strip()
  if not stripped:
    return True
  if stripped.endswith((".", "!", "?", '"', "'")):
    return False
  return len(stripped.split()) >= 6
