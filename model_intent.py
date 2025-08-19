"""
Train and serialize a Naive Bayes classifier for visa intents.
"""
import pickle
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

class VisaIntentModel:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('nb', MultinomialNB())
        ])

    def train(self, texts: List[str], labels: List[str]):
        self.pipeline.fit(texts, labels)

    def predict(self, text: str) -> str:
        return self.pipeline.predict([text])[0]

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump(self.pipeline, f)

    @classmethod
    def load(cls, path: str) -> 'VisaIntentModel':
        with open(path, 'rb') as f:
            pipeline = pickle.load(f)
        model = cls()
        model.pipeline = pipeline
        return model
