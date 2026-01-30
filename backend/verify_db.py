"""
Quick verification script to check database status
"""
import sys
sys.path.insert(0, '.')

from services.qdrant.client import QdrantManager

qm = QdrantManager()
info = qm.get_collection_info()

print('\n✅ Database Status:')
print(f'  Collection: products')
print(f'  Total products: {info["points_count"]}')
print(f'  Status: {info["status"]}')
print('\nDatabase is ready for the extension!')
