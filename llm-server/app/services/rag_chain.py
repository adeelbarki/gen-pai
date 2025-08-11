# app/services/rag_chain.py
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai import ChatOpenAI

rag_llm = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
)

rag_prompt = PromptTemplate(
    input_variables=["symptom", "history"],
    template="""You are a compassionate virtual doctor assistant.

                The patient has the symptom: **{symptom}**

                This is the current history so far:
                {history}

                Ask the next best follow-up question, clearly and naturally. Do not repeat prior questions. Only ask one question at a time.
            """
)

rag_chain = RunnablePassthrough() | rag_prompt | rag_llm
