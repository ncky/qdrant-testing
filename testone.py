import os
from time import perf_counter
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer

# Function to recursively read all .py files in a directory and extract functions and non-function lines
def read_files(file_path):
    start_time = perf_counter()

    data = []

    # Recursively search for all .py files in the file_path directory
    for root, dirs, files in os.walk(file_path):
        # Ignore folders starting with "." or "_"
        dirs[:] = [d for d in dirs if not d.startswith('.') or not d.startswith('_')]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    function_lines = []
                    function_name = ''
                    function_start = -1
                    # Iterate through each line in the file
                    for i, line in enumerate(lines):
                        # If we encounter a function definition, store the previous function's lines
                        if line.startswith('def '):
                            if function_start != -1:
                                data.append({
                                    'filepath': file_path,
                                    'function_name': function_name,
                                    'linenumbers': list(range(function_start, i)),
                                    'content': function_lines
                                })
                            function_name = line.split(' ')[1].split('(')[0]
                            function_start = i + 1
                            function_lines = []
                        else:
                            function_lines.append(line)
                    # Store the last function's lines
                    if function_start != -1:
                        data.append({
                            'filepath': file_path,
                            'function_name': function_name,
                            'linenumbers': list(range(function_start, len(lines) + 1)),
                            'content': function_lines
                        })
                    # Store any non-function lines in the file
                    non_function_lines = [line for line in lines if not line.startswith('def ')]
                    if non_function_lines:
                        data.append({
                            'filepath': file_path,
                            'function_name': '',
                            'linenumbers': list(range(1, len(non_function_lines) + 1)),
                            'content': non_function_lines
                        })

    end_time = perf_counter()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    return data


print("Loading Encoder")
# Load a pre-trained SentenceTransformer model to create embeddings
encoder = SentenceTransformer('all-MiniLM-L6-v2')
print("Creating in-memory Qdrant instance")
# Create an in-memory Qdrant instance for testing and CI/CD
qdrant = QdrantClient(":memory:")
# # OR
# Create a Qdrant instance that persists changes to disk for fast prototyping
# qdrant = QdrantClient(path="test.db")

project = "" #put project path here

print(f"Getting Project Data For \'{project}\'")
# Extract functions and non-function lines from all .py files in the project directory
project_data = read_files(project)
print(f"Got [{len(project_data)}] Functions.")
print("Creating Collection")

# Create a Qdrant collection to store functions
qdrant.recreate_collection(
    collection_name="my_project",
    vectors_config=models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(), # Vector size is defined by the used model
        distance=models.Distance.COSINE
    )
)

# Vectorize function and non-function lines and upload them to Qdrant
print("Vectorizing Content and Uploading to Qdrant")
start_time = perf_counter()
qdrant.upload_records(
    collection_name="my_project",
    records=[
        models.Record(
            id=idx,
            vector=encoder.encode('\n'.join(doc["content"])).tolist(),
            payload=doc
        ) for idx, doc in enumerate(project_data)
    ]
)
end_time = perf_counter()
print(f"Time taken: {end_time - start_time:.2f} seconds")

while True:
    sterm = input("Search: ")
    # Search for functions that are similar to the input query
    hits = qdrant.search(
        collection_name="my_project",
        query_vector=encoder.encode(sterm).tolist(),
        limit=3 # Return top 3 most similar functions
    )
    for hit in hits:
        print(hit.payload, "score:", hit.score)