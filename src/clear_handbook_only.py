import chromadb
from pathlib import Path

c = chromadb.PersistentClient(path=str(Path('chroma_db')))
try:
    c.delete_collection('handbook')
    print('✅ Deleted handbook collection')
except:
    print('handbook did not exist')
print('Direction collection untouched ✅')