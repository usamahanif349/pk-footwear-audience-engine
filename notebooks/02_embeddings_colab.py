# Google Colab, T4 GPU runtime. Turns each comment into a 768-number meaning vector.
# Output: data/raw/embeddings.npz (same order as comments_clean.csv)
!pip -q install sentence-transformers
from google.colab import files
import pandas as pd, numpy as np
from sentence_transformers import SentenceTransformer

print("Choose comments_clean.csv from your PC")
up = files.upload()
com = pd.read_csv(list(up)[0])

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
emb = model.encode(com.text.fillna("").astype(str).tolist(), batch_size=128,
                   show_progress_bar=True, normalize_embeddings=True)

np.savez_compressed("embeddings.npz", comment_id=com.comment_id.values, emb=emb.astype(np.float16))
print("Done:", emb.shape)
files.download("embeddings.npz")
