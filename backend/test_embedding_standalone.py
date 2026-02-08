#!/usr/bin/env python3
"""
Standalone test to verify embedding service works.
"""

import asyncio
from app.services.embedding_service import embedding_service


async def main():
    print("Testing Embedding Service...")
    print("-" * 50)

    # Test 1: Simple text embedding
    text = "Delicious margherita pizza with fresh basil and mozzarella"
    print(f"\nTest 1: Embedding text: '{text[:50]}...'")

    try:
        embedding = await embedding_service.embed(text)
        print(f"✓ Success! Generated embedding with dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # Test 2: Empty text should fail
    print("\nTest 2: Testing empty text (should fail)")
    try:
        await embedding_service.embed("")
        print("✗ Should have raised ValueError!")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")

    # Test 3: Batch embedding
    print("\nTest 3: Batch embedding")
    texts = [
        "Pizza margherita",
        "Chicken tikka masala",
        "Vegan burger with sweet potato fries",
    ]
    try:
        embeddings = await embedding_service.embed_batch(texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        for i, emb in enumerate(embeddings):
            print(f"  Text {i+1}: dimension={len(emb)}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
