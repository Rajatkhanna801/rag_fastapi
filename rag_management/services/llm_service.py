# app/rag_management/services/llm_service.py
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from rag_management.services.vector_store import VectorStoreService
from config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStoreService(db)
        self.llm_client = self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize the LLM client based on configured provider"""
        # This implementation uses OpenAI. Adjust based on your LLM provider.
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            return client
        except ImportError:
            logger.warning("OpenAI package not installed, using fallback client")
            
            # Implement a fallback client if needed
            class DummyLLM:
                def generate_answer(self, query, context):
                    return f"This is a dummy answer for: {query}. Context length: {len(context)}"
            
            return DummyLLM()
    
    async def answer_query(self, 
                         query: str, 
                         document_ids: Optional[List[str]] = None,
                         top_k: int = 5) -> Dict[str, Any]:
        """Generate an answer for a query using RAG"""
        # First, retrieve relevant context
        context_chunks = await self.vector_store.similarity_search(
            query=query,
            document_ids=document_ids,
            top_k=top_k
        )
        
        if not context_chunks:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "context": []
            }
        
        # Format context for the LLM
        context_text = "\n\n".join([f"CONTEXT {i+1}:\n{chunk['content']}" 
                                     for i, chunk in enumerate(context_chunks)])
        
        # Create prompt for the LLM
        prompt = self._create_rag_prompt(query, context_text)
        
        # Generate answer using LLM
        answer = await self._generate_completion(prompt)
        
        # Extract relevant document IDs
        document_ids = list(set(chunk["document_id"] for chunk in context_chunks))
        
        return {
            "answer": answer,
            "context": context_chunks
        }
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        """Create a RAG prompt for the LLM"""
        return f"""You are an AI assistant that answers questions based on the provided context. 
If you don't know the answer or if the context doesn't contain relevant information, 
say "I don't have enough information to answer this question."

CONTEXT:
{context}

USER QUESTION: {query}

Answer the question using ONLY the information provided in the context above. 
Be specific and provide a comprehensive answer based strictly on the relevant information in the context.
If the context doesn't contain the answer, simply state that you don't have enough information.
"""
    
    async def _generate_completion(self, prompt: str) -> str:
        """Generate a completion using the configured LLM"""
        try:
            # Implementation depends on your LLM provider
            # Example for OpenAI:
            if hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-4", 
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            
            # Example for a dummy client:
            elif hasattr(self.llm_client, 'generate_answer'):
                return self.llm_client.generate_answer(query=prompt, context=prompt)
            
            else:
                return "I couldn't process your question due to an issue with the language model."
                
        except Exception as e:
            logger.error(f"Error generating LLM completion: {e}")
            return "I encountered an error while processing your question. Please try again later."