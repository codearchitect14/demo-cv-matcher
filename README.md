\# CV Matcher – Job Recommendation System



\## Features

\- Hybrid recommendation (FAISS + filtering + ML re-ranking)

\- FastAPI-based backend

\- PostgreSQL storage

\- Embedding using `sentence-transformers`



\## Quick Start



```bash

conda create -n cvmatcher python=3.10

conda activate cvmatcher

pip install -r requirements.txt

uvicorn api.main:app --reload



