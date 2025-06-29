"""
Example of explicit graph construction using LangChain's RunnableSequence
"""

from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, Any

def create_explicit_graph():
    """Create an explicit graph with visible nodes and edges"""
    
    # Node 1: Safety Check
    safety_prompt = ChatPromptTemplate.from_template(
        "Is this question about Kambo? Answer YES or NO only.\nQuestion: {question}"
    )
    safety_llm = ChatOpenAI(temperature=0.0)
    safety_chain = safety_prompt | safety_llm | StrOutputParser()
    
    # Node 2: Kambo Response Generator
    kambo_prompt = ChatPromptTemplate.from_template(
        "You are a Kambo expert. Answer this question: {question}"
    )
    kambo_llm = ChatOpenAI(temperature=0.1)
    kambo_chain = kambo_prompt | kambo_llm | StrOutputParser()
    
    # Node 3: Medical Verifier
    medical_prompt = ChatPromptTemplate.from_template(
        "Verify this response is safe: {response}\nOriginal question: {question}"
    )
    medical_llm = ChatOpenAI(temperature=0.0)
    medical_chain = medical_prompt | medical_llm | StrOutputParser()
    
    # Edge 1: Route based on safety check
    def route_by_safety(inputs):
        safety_result = inputs["safety_check"].strip().upper()
        if "YES" in safety_result:
            return {"route": "kambo", "question": inputs["question"]}
        else:
            return {"route": "reject", "message": "Not Kambo-related"}
    
    # Edge 2: Combine question and response for verification
    def combine_for_verification(inputs):
        return {
            "question": inputs["question"],
            "response": inputs["kambo_response"]
        }
    
    # Build the explicit graph
    graph = (
        # Start with question
        {"question": RunnablePassthrough()}
        | {
            # Parallel safety check
            "safety_check": safety_chain,
            "question": RunnablePassthrough()
        }
        | RunnablePassthrough.assign(
            # Route based on safety
            routing=route_by_safety
        )
        | RunnablePassthrough.assign(
            # Generate Kambo response if safe
            kambo_response=lambda x: kambo_chain.invoke({"question": x["question"]}) 
            if x["routing"]["route"] == "kambo" else "Not applicable"
        )
        | RunnablePassthrough.assign(
            # Verify medical safety
            verification=combine_for_verification | medical_chain
        )
    )
    
    return graph

# Usage example:
# graph = create_explicit_graph()
# result = graph.invoke("What is Kambo?") 