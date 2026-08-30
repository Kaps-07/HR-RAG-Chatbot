from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from rag.llm import llm
from rag.prompts import prompt
from rag.vectorstore import vectorstore, has_documents


def build_context(top_docs_with_scores):
    """Join retrieved chunk texts into a single context string."""
    return "\n\n".join(doc.page_content for doc, _ in top_docs_with_scores)


def rag_search(query, k, history):
    """Run RAG with chat history and return answer, sources, and updated history."""
    if not has_documents():
        return {"error": "No documents found in database. Please upload files first."}, 400
    if not query:
        return {"error": "Query text required."}, 400

    # Retrieve relevant docs with scores
    top_docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)

    context = build_context(top_docs_with_scores)

    # Build chat history in LangChain message format
    chat_history = []
    for turn in history[-5:]:
        chat_history.append(HumanMessage(content=turn["user"]))
        chat_history.append(AIMessage(content=turn["bot"]))

    # Run LLM with prompt
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({
        "input": query,
        "context": context,
        "chat_history": chat_history,
    })

    history.append({"user": query, "bot": answer})

    results = [
        {"content": doc.page_content, "meta": doc.metadata, "score": round(1 - float(score), 3)}
        for doc, score in top_docs_with_scores
    ]

    return {"results": results, "answer": answer, "history": history}, 200
