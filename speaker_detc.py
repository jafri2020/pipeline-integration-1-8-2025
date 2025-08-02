from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import sounddevice as sd
from scipy.io.wavfile import write
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from record_audio import record #self built function
import pickle
import re
from collections import Counter

#load speaker embeddings
with open("known_embeddings.pkl", "rb") as f:
    known_embeddings = pickle.load(f)

def identify_speaker(input_emb, known_embs):
    names = list(known_embs.keys())
    embeddings = list(known_embs.values())
    similarities = cosine_similarity([input_emb], embeddings)[0]
    
    top_indices = np.argsort(similarities)[-5:][::-1]
    top_matches = [(names[i], similarities[i]) for i in top_indices]
    
    #standardizing the name 
    cleaned = [(re.sub(r'\d+', '', name), score) for name, score in top_matches]

    #minimum 2 instances should have probabilty over 0.75
    high_confidence = [score for name, score in cleaned if score >= 0.7]
    if len(high_confidence) >= 2:
        a=0 
    else:
        return "unknown"

    #removing numerics from the names and finding the most occurance
    names = [name for name, _ in cleaned]
    name_counts = Counter(names)
    most_common_name = name_counts.most_common(1)[0]
    return most_common_name[0]




