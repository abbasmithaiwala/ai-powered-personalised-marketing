"""
Core constants for the application.
"""

# Qdrant collection names
MENU_ITEM_EMBEDDINGS_COLLECTION = "menu_item_embeddings"
CUSTOMER_TASTE_PROFILES_COLLECTION = "customer_taste_profiles"

# Vector dimensions
# Using 384 for all-MiniLM-L6-v2 (local fallback)
# Can be updated to 1536 for text-embedding-3-small if using OpenAI embeddings
VECTOR_DIMENSION = 384

# Distance metric for vector similarity
VECTOR_DISTANCE = "Cosine"
