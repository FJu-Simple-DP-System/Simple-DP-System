import pandas as pd

df = pd.read_csv("wdbc.data", header=None)

# 去掉第二欄
col2 = df.columns[1]
new_order = [c for c in df.columns if c != col2] + [col2]

# 輸出新的資料集
df = df[new_order]
df.to_csv("wdbc_FT_GT.data", index=False, header=False)

df_no_first_col = df.iloc[:, 1:]   # 去掉第一欄
df = df_no_first_col

# 輸出新的資料集
df_no_first_col.to_csv("wdbc_FT_GT_no_first_col.data", index=False, header=False)

x = df.iloc[:, 0:-1]   # features
y = df.iloc[:, -1]     # label (e.g., 'M' / 'B')

print(x)
print(y)

from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(
    x, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
from diffprivlib.models import GaussianNB

epsilons = np.logspace(-2, 2, 50)
train_accuracy =    list()
predict_accuracy =  list()

for epsilon in epsilons:
    clf = GaussianNB(epsilon=epsilon)
    clf.fit(x_train, y_train)
    # training accuracy
    train_accuracy.append(clf.score(x_test, y_test))

    # predict accuracy
    y_pred = clf.predict(x_test)
    predict_accuracy.append(accuracy_score(y_test, y_pred))



from sklearn.naive_bayes import GaussianNB

gnb = GaussianNB()
gnb.fit(x_train, y_train)

y_pred = gnb.predict(x_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))



plt.figure(figsize=(10, 10))

plt.subplot(2, 1, 1)
plt.semilogx(epsilons, train_accuracy, linewidth=2, color='blue')
plt.title("Training Accuracy vs Epsilon")
plt.ylabel("Training Accuracy")
plt.grid(True)

plt.subplot(2, 1, 2)
plt.semilogx(epsilons, predict_accuracy, linewidth=2, color='green')
plt.title("Predict Accuracy vs Epsilon")
plt.xlabel("Epsilon")
plt.ylabel("Predict Accuracy")
plt.grid(True)

plt.tight_layout()
plt.show()
