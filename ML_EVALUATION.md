# ML evaluation

No labelled, licensed training dataset was present in the empty baseline workspace. SOVRIVA therefore uses an explainable deterministic taxonomy fallback in `sovriva/intelligence.py`, returning matched terms and a conservative confidence value. It does not claim precision, recall, F1, or a trained model.

The next valid ML step is to add a human-reviewed, licensed label set, split train/test data before fitting TF-IDF + Logistic Regression, and publish reproducible metrics and a confusion matrix. Until then, deterministic classification is the honest production path.
