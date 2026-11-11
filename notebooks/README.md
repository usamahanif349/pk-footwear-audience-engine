# Colab steps

These ran in Google Colab before the rest of the pipeline (they need internet access and a GPU).

1. **`01_collect_youtube_colab.py`**: collects videos and comments with the official YouTube Data API v3 and cleans them. The API key is kept in Colab Secrets (`YOUTUBE_API_KEY`), never in the code. Output: `videos.csv`, `comments.csv` (raw) and `videos_clean.csv`, `comments_clean.csv`.
2. **`02_embeddings_colab.py`**: multilingual sentence embeddings (`paraphrase-multilingual-mpnet-base-v2`) for every cleaned comment. Output: `embeddings.npz`.

After that, phone numbers, e-mails, @handles and order numbers were removed from the comment text (`src/engine/privacy.py`), and everything else runs locally with `python run_pipeline.py`.
