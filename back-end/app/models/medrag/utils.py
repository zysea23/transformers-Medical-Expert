# app/models/medrag/utils.py
from sentence_transformers.models import Transformer, Pooling
from sentence_transformers import SentenceTransformer
import os
import faiss
import json
import torch
import tqdm
import numpy as np
from pathlib import Path


corpus_names = {
   "PubMed": ["pubmed"],
   "Textbooks": ["textbooks"],
   "StatPearls": ["statpearls"],
   "Wikipedia": ["wikipedia"],
   "MedText": ["textbooks", "statpearls"],
   "MedCorp": ["pubmed", "textbooks", "statpearls", "wikipedia"],
}


retriever_names = {
   "BM25": ["bm25"],
   "Contriever": ["facebook/contriever"],
   "SPECTER": ["allenai/specter"],
   "MedCPT": ["ncbi/MedCPT-Query-Encoder"],
   "RRF-2": ["bm25", "ncbi/MedCPT-Query-Encoder"],
   "RRF-4": ["bm25", "facebook/contriever", "allenai/specter", "ncbi/MedCPT-Query-Encoder"]
}


def ends_with_ending_punctuation(s):
   ending_punctuation = ('.', '?', '!')
   return any(s.endswith(char) for char in ending_punctuation)


def concat(title, content):
   if ends_with_ending_punctuation(title.strip()):
       return title.strip() + " " + content.strip()
   else:
       return title.strip() + ". " + content.strip()


class CustomizeSentenceTransformer(SentenceTransformer): # change the default pooling "MEAN" to "CLS"


   def _load_auto_model(self, model_name_or_path, *args, **kwargs):
       """
       Creates a simple Transformer + CLS Pooling model and returns the modules
       """
       print("No sentence-transformers model found with name {}. Creating a new one with CLS pooling.".format(model_name_or_path))
       token = kwargs.get('token', None)
       cache_folder = kwargs.get('cache_folder', None)
       revision = kwargs.get('revision', None)
       trust_remote_code = kwargs.get('trust_remote_code', False)
       if 'token' in kwargs or 'cache_folder' in kwargs or 'revision' in kwargs or 'trust_remote_code' in kwargs:
           transformer_model = Transformer(
               model_name_or_path,
               cache_dir=cache_folder,
               model_args={"token": token, "trust_remote_code": trust_remote_code, "revision": revision},
               tokenizer_args={"token": token, "trust_remote_code": trust_remote_code, "revision": revision},
           )
       else:
           transformer_model = Transformer(model_name_or_path)
       pooling_model = Pooling(transformer_model.get_word_embedding_dimension(), 'cls')
       return [transformer_model, pooling_model]




def embed(chunk_dir, index_dir, model_name, **kwarg):
   save_dir = os.path.join(index_dir, "embedding")
   
   # Create save directory if it doesn't exist
   os.makedirs(save_dir, exist_ok=True)
  
   if "contriever" in model_name:
       model = SentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")
   else:
       model = CustomizeSentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")


   model.eval()


   fnames = sorted([fname for fname in os.listdir(chunk_dir) if fname.endswith(".jsonl")])


   with torch.no_grad():
       for fname in tqdm.tqdm(fnames):
           fpath = os.path.join(chunk_dir, fname)
           save_path = os.path.join(save_dir, fname.replace(".jsonl", ".npy"))
           if os.path.exists(save_path):
               continue
           # Check if file exists and is not empty
           if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
               continue

           with open(fpath, 'r', encoding='utf-8') as f:
               file_content = f.read().strip()
           
           if not file_content:
               continue
               
           texts = [json.loads(item) for item in file_content.split('\n')]
           if "specter" in model_name.lower():
               texts = [model.tokenizer.sep_token.join([item["title"], item["content"]]) for item in texts]
           elif "contriever" in model_name.lower():
               texts = [". ".join([item["title"], item["content"]]).replace('..', '.').replace("?.", "?") for item in texts]
           elif "medcpt" in model_name.lower():
               texts = [[item["title"], item["content"]] for item in texts]
           else:
               texts = [concat(item["title"], item["content"]) for item in texts]
           embed_chunks = model.encode(texts, **kwarg)
           np.save(save_path, embed_chunks)
       embed_chunks = model.encode([""], **kwarg)
   return embed_chunks.shape[-1]


def construct_index(index_dir, model_name, h_dim=768, HNSW=False, M=32):
   # Ensure directory exists
   os.makedirs(index_dir, exist_ok=True)
   
   metadata_path = os.path.join(index_dir, "metadatas.jsonl")
   with open(metadata_path, 'w', encoding='utf-8') as f:
       f.write("")
  
   if HNSW:
       M = M
       if "specter" in model_name.lower():
           index = faiss.IndexHNSWFlat(h_dim, M)
       else:
           index = faiss.IndexHNSWFlat(h_dim, M)
           index.metric_type = faiss.METRIC_INNER_PRODUCT
   else:
       if "specter" in model_name.lower():
           index = faiss.IndexFlatL2(h_dim)
       else:
           index = faiss.IndexFlatIP(h_dim)

   embed_dir = os.path.join(index_dir, "embedding")
   if not os.path.exists(embed_dir):
       os.makedirs(embed_dir, exist_ok=True)

   for fname in tqdm.tqdm(sorted(os.listdir(embed_dir))):
       embed_path = os.path.join(embed_dir, fname)
       if not fname.endswith('.npy') or not os.path.exists(embed_path):
           continue
           
       try:
           curr_embed = np.load(embed_path)
           index.add(curr_embed)
           with open(metadata_path, 'a+', encoding='utf-8') as f:
               f.write("\n".join([json.dumps({'index': i, 'source': fname.replace(".npy", "")}) for i in range(len(curr_embed))]) + '\n')
       except Exception as e:
           print(f"Error processing {fname}: {e}")


   faiss.write_index(index, os.path.join(index_dir, "faiss.index"))
   return index




class Retriever:


   def __init__(self, retriever_name="ncbi/MedCPT-Query-Encoder", corpus_name="textbooks", db_dir="./corpus", HNSW=False, **kwarg):
       self.retriever_name = retriever_name
       self.corpus_name = corpus_name

       # use Path to handle file paths
       self.db_dir = Path(db_dir)
       if not self.db_dir.exists():
           os.makedirs(self.db_dir, exist_ok=True)
           
       self.chunk_dir = self.db_dir / self.corpus_name / "chunk"
       if not self.chunk_dir.exists():
           print(f"Cloning the {self.corpus_name} corpus from Huggingface...")
           os.makedirs(self.chunk_dir.parent, exist_ok=True)
           os.system(f'git clone https://huggingface.co/datasets/MedRAG/{corpus_name} "{str(self.db_dir / self.corpus_name)}"')
           if self.corpus_name == "statpearls":
               print("Downloading the statpearls corpus from NCBI bookshelf...")
               download_path = str(self.db_dir / self.corpus_name)
               os.system(f'wget https://ftp.ncbi.nlm.nih.gov/pub/litarch/3d/12/statpearls_NBK430685.tar.gz -P "{download_path}"')
               os.system(f'tar -xzvf "{download_path}/statpearls_NBK430685.tar.gz" -C "{download_path}"')
               print("Chunking the statpearls corpus...")
               os.system("python src/data/statpearls.py")
               
       self.index_dir = self.db_dir / self.corpus_name / "index" / self.retriever_name.replace("Query-Encoder", "Article-Encoder")
       
       if "bm25" in self.retriever_name.lower():
           from pyserini.search.lucene import LuceneSearcher
           self.metadatas = None
           self.embedding_function = None
           if self.index_dir.exists():
               self.index = LuceneSearcher(str(self.index_dir))
           else:
               os.makedirs(self.index_dir, exist_ok=True)
               os.system(f'python -m pyserini.index.lucene --collection JsonCollection --input "{str(self.chunk_dir)}" --index "{str(self.index_dir)}" --generator DefaultLuceneDocumentGenerator --threads 16')
               self.index = LuceneSearcher(str(self.index_dir))
       else:
           index_file = self.index_dir / "faiss.index"
           metadata_file = self.index_dir / "metadatas.jsonl"
           
           if index_file.exists():
               self.index = faiss.read_index(str(index_file))
               
               # Safely read metadata
               if metadata_file.exists():
                   with open(metadata_file, 'r', encoding='utf-8') as f:
                       content = f.read().strip()
                   if content:
                       self.metadatas = [json.loads(line) for line in content.split('\n')]
                   else:
                       self.metadatas = []
               else:
                   self.metadatas = []
           else:
               print(f"[In progress] Embedding the {self.corpus_name} corpus with the {self.retriever_name.replace('Query-Encoder', 'Article-Encoder')} retriever...")
               embedding_dir = self.index_dir / "embedding"
               
               if self.corpus_name in ["textbooks", "pubmed", "wikipedia"] and self.retriever_name in ["allenai/specter", "facebook/contriever", "ncbi/MedCPT-Query-Encoder"] and not embedding_dir.exists():
                   print(f"[In progress] Downloading the {self.corpus_name} embeddings given by the {self.retriever_name.replace('Query-Encoder', 'Article-Encoder')} model...")
                   os.makedirs(self.index_dir, exist_ok=True)
                   
                   # Windows compatible download commands
                   if self.corpus_name == "textbooks":
                       if self.retriever_name == "allenai/specter":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EYRRpJbNDyBOmfzCOqfQzrsBwUX0_UT8-j_geDPcVXFnig?download=1')
                       elif self.retriever_name == "facebook/contriever":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EQqzldVMCCVIpiFV4goC7qEBSkl8kj5lQHtNq8DvHJdAfw?download=1')
                       elif self.retriever_name == "ncbi/MedCPT-Query-Encoder":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EQ8uXe4RiqJJm0Tmnx7fUUkBKKvTwhu9AqecPA3ULUxUqQ?download=1')
                   elif self.corpus_name == "pubmed":
                       if self.retriever_name == "allenai/specter":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/Ebz8ySXt815FotxC1KkDbuABNycudBCoirTWkKfl8SEswA?download=1')
                       elif self.retriever_name == "facebook/contriever":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EWecRNfTxbRMnM0ByGMdiAsBJbGJOX_bpnUoyXY9Bj4_jQ?download=1')
                       elif self.retriever_name == "ncbi/MedCPT-Query-Encoder":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EVCuryzOqy5Am5xzRu6KJz4B6dho7Tv7OuTeHSh3zyrOAw?download=1')
                   elif self.corpus_name == "wikipedia":
                       if self.retriever_name == "allenai/specter":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/Ed7zG3_ce-JOmGTbgof3IK0BdD40XcuZ7AGZRcV_5D2jkA?download=1')
                       elif self.retriever_name == "facebook/contriever":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/ETKHGV9_KNBPmDM60MWjEdsBXR4P4c7zZk1HLLc0KVaTJw?download=1')
                       elif self.retriever_name == "ncbi/MedCPT-Query-Encoder":
                           os.system(f'wget -O "{str(self.index_dir / "embedding.zip")}" https://myuva-my.sharepoint.com/:u:/g/personal/hhu4zu_virginia_edu/EXoxEANb_xBFm6fa2VLRmAcBIfCuTL-5VH6vl4GxJ06oCQ?download=1')
                           
                   # Use cross-platform approach to unzip and delete files
                   os.system(f'unzip "{str(self.index_dir / "embedding.zip")}" -d "{str(self.index_dir)}"')
                   if os.path.exists(str(self.index_dir / "embedding.zip")):
                       os.remove(str(self.index_dir / "embedding.zip"))
                   h_dim = 768
               else:
                   h_dim = embed(chunk_dir=str(self.chunk_dir), index_dir=str(self.index_dir), model_name=self.retriever_name.replace("Query-Encoder", "Article-Encoder"), **kwarg)


               print(f"[In progress] Embedding finished! The dimension of the embeddings is {h_dim}.")
               self.index = construct_index(index_dir=str(self.index_dir), model_name=self.retriever_name.replace("Query-Encoder", "Article-Encoder"), h_dim=h_dim, HNSW=HNSW)
               print("[Finished] Corpus indexing finished!")
               
               # read metadata
               if metadata_file.exists():
                   with open(metadata_file, 'r', encoding='utf-8') as f:
                       content = f.read().strip()
                   if content:
                       self.metadatas = [json.loads(line) for line in content.split('\n')]
                   else:
                       self.metadatas = []
               else:
                   self.metadatas = []
                   
           if "contriever" in self.retriever_name.lower():
               self.embedding_function = SentenceTransformer(self.retriever_name, device="cuda" if torch.cuda.is_available() else "cpu")
           else:
               self.embedding_function = CustomizeSentenceTransformer(self.retriever_name, device="cuda" if torch.cuda.is_available() else "cpu")
           self.embedding_function.eval()


   def get_relevant_documents(self, question, k=32, id_only=False, **kwarg):
       assert type(question) == str
       question = [question]


       if "bm25" in self.retriever_name.lower():
           res_ = [[]]
           hits = self.index.search(question[0], k=k)
           res_[0].append(np.array([h.score for h in hits]))
           ids = [h.docid for h in hits]
           indices = [{"source": '_'.join(h.docid.split('_')[:-1]), "index": eval(h.docid.split('_')[-1])} for h in hits]
       else:
           with torch.no_grad():
               query_embed = self.embedding_function.encode(question, **kwarg)
           res_ = self.index.search(query_embed, k=k)
           
           # Check if search results are empty
           if len(res_[1][0]) == 0:
               return [], []
               
           ids = ['_'.join([self.metadatas[i]["source"], str(self.metadatas[i]["index"])]) for i in res_[1][0]]
           indices = [self.metadatas[i] for i in res_[1][0]]


       scores = res_[0][0].tolist()
      
       if id_only:
           return [{"id":i} for i in ids], scores
       else:
           return self.idx2txt(indices), scores


   def idx2txt(self, indices): # return List of Dict of str
       '''
       Input: List of Dict( {"source": str, "index": int} )
       Output: List of str
       '''
       result = []
       for i in indices:
           jsonl_path = self.chunk_dir / f"{i['source']}.jsonl"
           if not jsonl_path.exists():
               # if the document is missing, return a placeholder
               result.append({"title": "Missing document", "content": "Document not found"})
               continue
               
           with open(jsonl_path, 'r', encoding='utf-8') as f:
               content = f.read().strip()
               
           if not content:
               result.append({"title": "Empty document", "content": "Document is empty"})
               continue
               
           lines = content.split('\n')
           if i["index"] >= len(lines):
               result.append({"title": "Index error", "content": f"Index {i['index']} out of range"})
               continue
               
           try:
               result.append(json.loads(lines[i["index"]]))
           except json.JSONDecodeError:
               result.append({"title": "Parse error", "content": "Could not parse document"})
               
       return result


class RetrievalSystem:


   def __init__(self, retriever_name="MedCPT", corpus_name="Textbooks", db_dir="./corpus", HNSW=False, cache=False):
       self.retriever_name = retriever_name
       self.corpus_name = corpus_name
       assert self.corpus_name in corpus_names
       assert self.retriever_name in retriever_names
       self.retrievers = []
       for retriever in retriever_names[self.retriever_name]:
           self.retrievers.append([])
           for corpus in corpus_names[self.corpus_name]:
               self.retrievers[-1].append(Retriever(retriever, corpus, db_dir, HNSW=HNSW))
       self.cache = cache
       if self.cache:
           self.docExt = DocExtracter(cache=True, corpus_name=self.corpus_name, db_dir=db_dir)
       else:
           self.docExt = None
  
   def retrieve(self, question, k=32, rrf_k=100, id_only=False):
       '''
           Given questions, return the relevant snippets from the corpus
       '''
       assert type(question) == str


       output_id_only = id_only
       if self.cache:
           id_only = True


       texts = []
       scores = []


       if "RRF" in self.retriever_name:
           k_ = max(k * 2, 100)
       else:
           k_ = k
       for i in range(len(retriever_names[self.retriever_name])):
           texts.append([])
           scores.append([])
           for j in range(len(corpus_names[self.corpus_name])):
               t, s = self.retrievers[i][j].get_relevant_documents(question, k=k_, id_only=id_only)
               texts[-1].append(t)
               scores[-1].append(s)
       texts, scores = self.merge(texts, scores, k=k, rrf_k=rrf_k)
       if self.cache:
           texts = self.docExt.extract(texts)
       return texts, scores


   def merge(self, texts, scores, k=32, rrf_k=100):
       '''
           Merge the texts and scores from different retrievers
       '''
       RRF_dict = {}
       for i in range(len(retriever_names[self.retriever_name])):
           texts_all, scores_all = None, None
           for j in range(len(corpus_names[self.corpus_name])):
               if texts_all is None:
                   texts_all = texts[i][j]
                   scores_all = scores[i][j]
               else:
                   texts_all = texts_all + texts[i][j]
                   scores_all = scores_all + scores[i][j]
           if "specter" in retriever_names[self.retriever_name][i].lower():
               sorted_index = np.array(scores_all).argsort()
           else:
               sorted_index = np.array(scores_all).argsort()[::-1]
           texts[i] = [texts_all[i] for i in sorted_index]
           scores[i] = [scores_all[i] for i in sorted_index]
           for j, item in enumerate(texts[i]):
               if item["id"] in RRF_dict:
                   RRF_dict[item["id"]]["score"] += 1 / (rrf_k + j + 1)
                   RRF_dict[item["id"]]["count"] += 1
               else:
                   RRF_dict[item["id"]] = {
                       "id": item["id"],
                       "title": item.get("title", ""),
                       "content": item.get("content", ""),
                       "score": 1 / (rrf_k + j + 1),
                       "count": 1
                       }
       RRF_list = sorted(RRF_dict.items(), key=lambda x: x[1]["score"], reverse=True)
       if len(texts) == 1:
           texts = texts[0][:k]
           scores = scores[0][:k]
       else:
           texts = [dict((key, item[1][key]) for key in ("id", "title", "content")) for item in RRF_list[:k]]
           scores = [item[1]["score"] for item in RRF_list[:k]]
       return texts, scores
  


class DocExtracter:
  
   def __init__(self, db_dir="./corpus", cache=False, corpus_name="MedCorp"):
       self.db_dir = Path(db_dir)
       self.cache = cache
       print("Initializing the document extracter...")
       for corpus in corpus_names[corpus_name]:
           corpus_chunk_dir = self.db_dir / corpus / "chunk"
           if not corpus_chunk_dir.exists():
               print(f"Cloning the {corpus} corpus from Huggingface...")
               os.makedirs(corpus_chunk_dir.parent, exist_ok=True)
               os.system(f'git clone https://huggingface.co/datasets/MedRAG/{corpus} "{str(self.db_dir / corpus)}"')
               if corpus == "statpearls":
                   print("Downloading the statpearls corpus from NCBI bookshelf...")
                   download_path = str(self.db_dir / corpus)
                   os.system(f'wget https://ftp.ncbi.nlm.nih.gov/pub/litarch/3d/12/statpearls_NBK430685.tar.gz -P "{download_path}"')
                   os.system(f'tar -xzvf "{download_path}/statpearls_NBK430685.tar.gz" -C "{download_path}"')
                   print("Chunking the statpearls corpus...")
                   os.system("python src/data/statpearls.py")
       
       id2text_path = self.db_dir / f"{corpus_name}_id2text.json"
       id2path_path = self.db_dir / f"{corpus_name}_id2path.json"
       
       if self.cache:
           if id2text_path.exists():
               with open(id2text_path, 'r', encoding='utf-8') as f:
                   self.dict = json.load(f)
           else:
               self.dict = {}
               for corpus in corpus_names[corpus_name]:
                   corpus_chunk_dir = self.db_dir / corpus / "chunk"
                   if corpus_chunk_dir.exists():
                       for fname in tqdm.tqdm(sorted(os.listdir(corpus_chunk_dir))):
                           fname_path = corpus_chunk_dir / fname
                           if not fname_path.exists() or os.path.getsize(fname_path) == 0:
                               continue
                               
                           with open(fname_path, 'r', encoding='utf-8') as f:
                               content = f.read().strip()
                               
                           if not content:
                               continue
                               
                           for i, line in enumerate(content.split('\n')):
                               try:
                                   item = json.loads(line)
                                   _ = item.pop("contents", None)
                                   if "id" in item:
                                       self.dict[item["id"]] = item
                               except json.JSONDecodeError:
                                   continue
                                   
               with open(id2text_path, 'w', encoding='utf-8') as f:
                   json.dump(self.dict, f)
       else:
           if id2path_path.exists():
               with open(id2path_path, 'r', encoding='utf-8') as f:
                   self.dict = json.load(f)
           else:
               self.dict = {}
               for corpus in corpus_names[corpus_name]:
                   corpus_chunk_dir = self.db_dir / corpus / "chunk"
                   if corpus_chunk_dir.exists():
                       for fname in tqdm.tqdm(sorted(os.listdir(corpus_chunk_dir))):
                           fname_path = corpus_chunk_dir / fname
                           if not fname_path.exists() or os.path.getsize(fname_path) == 0:
                               continue
                               
                           with open(fname_path, 'r', encoding='utf-8') as f:
                               content = f.read().strip()
                               
                           if not content:
                               continue
                               
                           for i, line in enumerate(content.split('\n')):
                               try:
                                   item = json.loads(line)
                                   if "id" in item:
                                       self.dict[item["id"]] = {"fpath": str(Path(corpus) / "chunk" / fname), "index": i}
                               except json.JSONDecodeError:
                                   continue
                                   
               with open(id2path_path, 'w', encoding='utf-8') as f:
                   json.dump(self.dict, f, indent=4)
                   
       print("Initialization finished!")
  
   def extract(self, ids):
       if self.cache:
           output = []
           for i in ids:
               item_id = i if type(i) == str else i.get("id")
               if item_id in self.dict:
                   output.append(self.dict[item_id])
               else:
                   # if the document is missing, return a placeholder
                   output.append({"title": "Unknown document", "content": "Document not found"})
       else:
           output = []
           for i in ids:
               item_id = i if type(i) == str else i.get("id")
               if item_id in self.dict:
                   item = self.dict[item_id]
                   fpath = self.db_dir / item["fpath"]
                   
                   if not fpath.exists():
                       output.append({"title": "Missing file", "content": f"File {item['fpath']} not found"})
                       continue
                       
                   try:
                       with open(fpath, 'r', encoding='utf-8') as f:
                           content = f.read().strip()
                           
                       if not content:
                           output.append({"title": "Empty file", "content": "File is empty"})
                           continue
                           
                       lines = content.split('\n')
                       if item["index"] >= len(lines):
                           output.append({"title": "Index error", "content": f"Index {item['index']} out of range"})
                           continue
                           
                       output.append(json.loads(lines[item["index"]]))
                   except Exception as e:
                       output.append({"title": "Error", "content": f"Error extracting document: {str(e)}"})
               else:
                   output.append({"title": "Unknown document", "content": "Document ID not found"})
       return output