import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from app.docs_writer import write_docx_report
from uuid import uuid4


def retrieve_rag_context(requirement, rag_knowledge_path, k=5):
    # Load RAG knowledge base and build vector store    
    loader = TextLoader(rag_knowledge_path, encoding='utf-8')
    docs = loader.load()    
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(split_docs, embeddings)
    # Retrieve most relevant knowledge snippets
    results = db.similarity_search(requirement, k=k)
    context = "\n".join([doc.page_content for doc in results])
    return context

def agentic_expand(requirement, context, template):
    """
    Generate a detailed SAP Technical Specification Document using a structured prompt and context.
    """
    system_prompt = f"""
You are a senior SAP ABAP technical designer. Analyse the requirement using the comprehensive pointers in CONTEXT and emulate the style and depth found in any provided sample SAP Technical Specification Documents.
Create a professional, detailed SAP Technical Specification Document (min 2000 words), fully formatted as per the TEMPLATE.
For sections involving code or pseudo-code, do NOT create or copy the code anywhere. Instead, explain the flow in logical step, 
-provide a clear, SAP-project-relevant technical explanation of what it does and why it is necessary.
- which tables are joined with which fields ....and so on in English readable format.
This should continue step by step, until all logic is fully explained and auditable.
Don't insert the code inside the document.

INSTRUCTIONS:
- Use ONLY information from CONTEXT, REQUIREMENT, and TEMPLATE.
- For each pointer/section in the technical spec TEMPLATE, write clear, exhaustive bullet points, referencing SAP ABAP code, SAP business processes, technical notes, and explicit implementation explanations.
- Do not produce generic text—each section should be filled as if for a real SAP project handover, including code and process specifics.
- Use consistent SAP terminology and best practice explanations.

## CONTEXT:
{context}

## REQUIREMENT:
{requirement}

## TEMPLATE:
{template}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content":
            "Generate the complete SAP technical specification strictly formatted as per TEMPLATE. Each section MUST be expanded with project-realistic technical content, ABAP pseudo-code, business/technical justifications, and implementation notes."
        }
    ]

    llm = ChatOpenAI(temperature=0.3, model="gpt-4.1")
    response = llm.invoke(messages)
    # Depending on your LLM library, adapt as needed:
    if hasattr(response, "content"):
        output = response.content
    elif isinstance(response, dict) and "content" in response:
        output = response["content"]
    else:
        output = response
    return output

def create_spec_document(requirement, template):
    """
    Main generator function.
    Reads requirement and template strings, uses RAG + agentic/expert expansion,
    and returns path to generated .docx file.
    """
    # Step 1: RAG contextualization
    rag_knowledge_path = os.path.join(os.path.dirname(__file__), "rag_know1.txt")
    context = retrieve_rag_context(requirement, rag_knowledge_path)

    # Step 2: AGENTIC/LLM expansion (can add even more reasoning/tools here)
    detailed_doc_text = agentic_expand(requirement, context, template)

    # Step 3: DOCX Generation
    output_path = f"output/spec_{uuid4().hex}.docx"
    write_docx_report(detailed_doc_text, template, output_path)
    return output_path