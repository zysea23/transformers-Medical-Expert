# app/models/medrag/medrag.py
import os
import re
import json
import tqdm
from app.models.medrag.utils import RetrievalSystem, DocExtracter


class MedRAG:
    def __init__(self, llm_name="local-model", rag=True, retriever_name="MedCPT", corpus_name="Textbooks", db_dir="./corpus", corpus_cache=False, HNSW=False):
        """
        Initialize MedRAG with simplified configuration
        
        Args:
            llm_name: Model name (ignored as we're using local API)
            rag: Whether to use RAG or not
            retriever_name: Name of the retriever to use
            corpus_name: Name of the corpus to use
            db_dir: Directory where corpus data is stored
            corpus_cache: Whether to cache corpus in memory
            HNSW: Whether to use HNSW index for retrieval
        """
        self.llm_name = llm_name
        self.rag = rag
        self.retriever_name = retriever_name
        self.corpus_name = corpus_name
        self.db_dir = db_dir
        self.docExt = None
        
        # Initialize retrieval system if RAG is enabled
        if rag:
            self.retrieval_system = RetrievalSystem(
                self.retriever_name, 
                self.corpus_name, 
                self.db_dir, 
                cache=corpus_cache, 
                HNSW=HNSW
            )
        else:
            self.retrieval_system = None
            
        # Define system messages for prompts
        self.system_messages = {
            "cot_system": "You are a helpful medical expert, and your task is to answer medical questions. Please provide your answers in natural language, explaining concepts clearly for a general audience. Make sure to be accurate, informative, and educational.",
            
            "medrag_system": "You are a helpful medical expert, and your task is to answer medical questions using the relevant documents. Please provide your answers in natural language, explaining concepts clearly for a general audience. When answering general knowledge questions about medical terms, provide a definition, explanation of the concept, normal ranges if applicable, and clinical significance. Make sure to be accurate, informative, and educational."
        }

    def generate(self, messages, **kwargs):
        """
        Placeholder for the generate method that will be overridden by RAGHandler
        
        Args:
            messages: List of messages for the LLM
            kwargs: Additional parameters for the LLM
            
        Returns:
            str: Generated response
        """
        # This method is intentionally left empty
        # It will be overridden by the _generate_with_lmstudio method in RAGHandler
        pass

    def medrag_answer(self, question, options=None, k=32, rrf_k=100, snippets=None, snippets_ids=None, **kwargs):
        """
        Answer a question using MedRAG
        
        Args:
            question: The question to answer
            options: Optional choices for multiple choice questions
            k: Number of snippets to retrieve
            rrf_k: Parameter for reciprocal rank fusion
            snippets: Pre-retrieved snippets (optional)
            snippets_ids: Pre-retrieved snippet IDs (optional)
            
        Returns:
            tuple: (answer, snippets, scores)
        """
        # Format options if provided
        options_formatted = ''
        if options is not None:
            options_formatted = '\n'.join([key+". "+options[key] for key in sorted(options.keys())])

        # Retrieve relevant snippets if RAG is enabled
        if self.rag:
            if snippets is not None:
                retrieved_snippets = snippets[:k]
                scores = []
            elif snippets_ids is not None:
                if self.docExt is None:
                    self.docExt = DocExtracter(db_dir=self.db_dir, cache=True, corpus_name=self.corpus_name)
                retrieved_snippets = self.docExt.extract(snippets_ids[:k])
                scores = []
            else:
                assert self.retrieval_system is not None
                retrieved_snippets, scores = self.retrieval_system.retrieve(question, k=k, rrf_k=rrf_k)

            # Format contexts for the LLM
            contexts = ["Document [{:d}] (Title: {:s}) {:s}".format(
                idx, retrieved_snippets[idx]["title"], retrieved_snippets[idx]["content"]
            ) for idx in range(len(retrieved_snippets))]
            
            if len(contexts) == 0:
                contexts = [""]
        else:
            retrieved_snippets = []
            scores = []
            contexts = [""]

        # Generate answers
        if not self.rag:
            # For non-RAG approach
            prompt_cot = f"""
Here is the question:
{question}

Here are the potential choices:
{options_formatted}

Please think step-by-step and provide a clear, educational answer:
"""
            messages = [
                {"role": "system", "content": self.system_messages["cot_system"]},
                {"role": "user", "content": prompt_cot}
            ]
            ans = self.generate(messages, **kwargs)
            answer = re.sub(r"\s+", " ", ans)
        else:
            # For RAG approach - just use the first context to avoid returning a list
            context = contexts[0] if contexts else ""
            prompt_medrag = f"""
Here are the relevant documents:
{context}

Here is the question:
{question}

Here are the potential choices:
{options_formatted}

Please provide a comprehensive and educational answer in natural language, explaining the concept clearly for a general audience:
"""
            messages = [
                {"role": "system", "content": self.system_messages["medrag_system"]},
                {"role": "user", "content": prompt_medrag}
            ]
            ans = self.generate(messages, **kwargs)
            answer = re.sub(r"\s+", " ", ans)
        
        return answer, retrieved_snippets, scores

    def answer(self, *args, **kwargs):
        """
        Default answer method that uses medrag_answer
        """
        return self.medrag_answer(*args, **kwargs)