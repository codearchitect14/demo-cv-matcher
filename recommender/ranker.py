from sklearn.linear_model import LogisticRegression

class Ranker:
    def __init__(self):
        self.model = LogisticRegression()

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict_proba(X)[:, 1]
