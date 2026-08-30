from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def split_text(content, filename):
    """Split text into chunks with filename metadata."""
    return splitter.create_documents(
        texts=[content],
        metadatas=[{"filename": filename}]
    )
