import os
import chromadb
from chromadb.utils import embedding_functions

# Wyłączamy telemetrię ChromaDB (szybciej na Windows)
os.environ["ANONYMIZED_TELEMETRY"] = "False"


class ProjectMemory:
    def __init__(self, project_path):
        print(f"🧠 Inicjalizacja Pamięci Projektu: {project_path}")
        self.project_path = project_path
        self.client = chromadb.Client()
        # Lekki model embeddowania (działa szybko na CPU)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

        # Tworzymy (lub czyścimy) kolekcję
        try:
            self.client.delete_collection(name="project_code")
        except:
            pass
        self.collection = self.client.create_collection(name="project_code", embedding_function=self.embedder)

        self.index_project()

    def index_project(self):
        print("📥 Skanowanie i indeksowanie plików...")
        ids = []
        documents = []
        metadatas = []

        # Ignorujemy śmieci
        ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', 'moje_ai_adaptery', '.idea', 'build', 'dist'}
        extensions = ('.py', '.js', '.java', '.cpp', '.php', '.html', '.sql')

        count = 0
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if file.endswith(extensions):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if not content.strip(): continue

                            # Tniemy na kawałki (Chunki) po 1000 znaków z zakładką 100
                            # Żeby model łapał kontekst funkcji
                            chunk_size = 1000
                            overlap = 100

                            for i in range(0, len(content), chunk_size - overlap):
                                chunk = content[i: i + chunk_size]
                                chunk_id = f"{file}_{i}"

                                ids.append(chunk_id)
                                documents.append(chunk)
                                metadatas.append({"path": path, "filename": file})
                                count += 1
                    except:
                        pass

        # Wrzucamy do bazy paczkami (batching)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end]
            )

        print(f"✅ Pamięć gotowa. Zindeksowano {count} fragmentów kodu.")

    def query(self, query_text, n_results=3):
        """Szuka powiązanych fragmentów kodu w projekcie."""
        if not query_text: return ""

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        context_str = ""
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                context_str += f"\n--- KONTEKST Z PLIKU: {meta['filename']} ---\n{doc}\n"

        return context_str


if __name__ == "__main__":
    # Test
    mem = ProjectMemory(os.getcwd())
    print(mem.query("def audit_file"))