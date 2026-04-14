import asyncio
import os

from sqlalchemy import text

from langfuse.openai import OpenAI
from langfuse import observe

from langchain_core.documents import Document
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings
from ragas.testset import TestsetGenerator

from models import engine

from dotenv import load_dotenv
load_dotenv()



def fetch_chunks(limit=200):

    query = text("""
        SELECT content 
        FROM service_chunks 
        ORDER BY RANDOM() 
        LIMIT :limit
    """
    )
    docs = []
    with engine.connect() as conn:
        result = conn.execute(
            query, {"limit": limit}
            
        )
        
        for row in result:
            docs.append(Document(
                page_content=row.content
            ))

    return docs


@observe()
async def generate_testset(docs, test_size=50):
    client = OpenAI()

    llm = llm_factory("gpt-4o", client=client)
    openai_embeddings = OpenAIEmbeddings(client=client, model="text-embedding-3-small")

    generator = TestsetGenerator(
        llm=llm,
        embedding_model=openai_embeddings
    )

    from ragas.testset.synthesizers.single_hop.specific import SingleHopSpecificQuerySynthesizer

    distribution = [(
        SingleHopSpecificQuerySynthesizer(
            llm=llm,
            llm_context="Sempre gere perguntas e respostas em portugues brasileiro (pt-BR).",
        ),
        1.0,
    )]

    for query, _ in distribution:
        prompts = await query.adapt_prompts(
            "brazilian portuguese",
            llm=llm,
            adapt_instruction=True,
        )
        query.set_prompts(**prompts)


    testset = generator.generate_with_langchain_docs(
        docs, 
        testset_size=test_size, 
        query_distribution=distribution
    )
    
    return testset.to_pandas()


if __name__ == "__main__":
    chunks = fetch_chunks()
    testset_df =  asyncio.run(generate_testset(chunks, test_size=2))
    testset_df.to_csv("testset.csv", index=False)
