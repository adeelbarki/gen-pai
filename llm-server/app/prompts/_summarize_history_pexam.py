from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

def _summarize(context_text: str) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are a clinical summarizer. Produce a concise 3–4 line handover summary. "
             "Focus on: chief concerns, salient positives/negatives from chat, key exam findings, "
             "and any clear next steps mentioned. No PHI, no speculation, max 4 lines."),
            ("human", "Use only this context:\n\n{context}")
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context_text}).strip()