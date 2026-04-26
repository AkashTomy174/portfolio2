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
Keep answers under 150 words unless the user asks for detail."""


class LlmService:
  def __init__(self, api_key: str | None, model: str) -> None:
    self.model = model
    self.client = genai.Client(api_key=api_key) if api_key else None

  def answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
    if not self.client:
      return _offline_answer(chunks)

    context = "\n\n".join(
      f"Source: {chunk.source} | Topic: {chunk.topic}\n{chunk.text}"
      for chunk in chunks
    )

    try:
      response = self.client.models.generate_content(
        model=self.model,
        contents=f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}",
        config=types.GenerateContentConfig(
          max_output_tokens=260,
          temperature=0.4,
        ),
      )
      return response.text.strip()
    except Exception as exc:
      logger.warning("Gemini chat failed; using offline answer. error=%s", exc)
      return _offline_answer(chunks)


def _offline_answer(chunks: list[RetrievedChunk]) -> str:
  if not chunks:
    return "I don't have that information - reach out to Akash directly."
  return chunks[0].text
