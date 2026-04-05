import chromadb
from pathlib import Path

c = chromadb.PersistentClient(path=str(Path('chroma_db')))
try:
    c.delete_collection('direction')
    print('✅ Deleted direction collection')
except:
    print('direction did not exist')
print('Handbook untouched ✅')