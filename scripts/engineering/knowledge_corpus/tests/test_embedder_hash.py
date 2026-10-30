from scripts.engineering.knowledge_corpus.embedder import HashEmbedder
from scripts.engineering.knowledge_corpus.config import EMBEDDING_DIM


def test_hash_embedder_dim_and_normalized() -> None:
    emb = HashEmbedder()
    vecs = emb.embed(["hello world", "hello world", "other"])
    assert len(vecs) == 3
    assert all(len(v) == EMBEDDING_DIM for v in vecs)
    # identical inputs -> identical vectors
    assert vecs[0] == vecs[1]
    assert vecs[0] != vecs[2]
    # roughly unit length
    norm = sum(x * x for x in vecs[0]) ** 0.5
    assert 0.99 <= norm <= 1.01
