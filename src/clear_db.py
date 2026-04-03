import chromadb
from pathlib import Path

c = chromadb.PersistentClient(path=str(Path('chroma_db')))
for name in ['direction', 'handbook']:
    try:
        c.delete_collection(name)
        print(f'Deleted {name}')
    except:
        print(f'{name} did not exist')
print('Done!')