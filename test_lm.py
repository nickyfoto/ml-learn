import pytest
from pytest import approx

import numpy as np
from sklearn import linear_model, datasets
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from lm import LinearRegression, SGDRegressor


boston = datasets.load_boston()
X = boston.data
y = boston.target

reg = LinearRegression()
skreg = linear_model.LinearRegression()

sgd = SGDRegressor()
sksgd = linear_model.SGDRegressor(random_state=0, verbose=0, #shuffle=False, 
                                        penalty='none')

scaled_X = StandardScaler().fit_transform(X) 




test1 = X, y, reg, skreg
test2 = scaled_X, y, sgd, sksgd
ids = ['boston, myLR, skLR',
       'scaled boston, mySGD, skSGD']

# pytest -vv --html=report.html --capture=sys


@pytest.mark.parametrize("X, y, reg1, reg2", [
                          test1,
                          test2
                          ], 
                          ids=ids)
class TestSK:

    def _print_results(self, clf_names, metric, description, preds):
        metrics = []
        for i, name in enumerate(clf_names):
            m = metric(self.y_train, preds[i])
            print(f"{name} {description}", m)
            metrics.append(m)
        print('abs diff: ', np.abs(metrics[0] - metrics[1]))
        # assert metrics[0] == approx(metrics[1])
        assert metrics[0] == approx(metrics[1], abs = 1e-1)
        print()

    def compare_performance(self, metrics, descriptions):
        clf_names = ['mylearn', 'sklearn']
        
        for name, clf in zip(clf_names, [self.learn, self.sk]):
            print(name, clf)
        print()
        preds = [clf.predict(self.X_train) for clf in [self.learn_clf, self.sk_clf]]

        for i, metric in enumerate(metrics):
            self._print_results(clf_names, metric, descriptions[i], preds)


    def compare_attributes(self, attributes):
        for attribute in attributes:
            print('comparing', attribute)
            m, s = getattr(self.learn_clf, attribute), getattr(self.sk_clf, attribute)
            print('mylearn:\n', m)
            print('sklearn:\n', s)
            print('abs diff:\n', np.abs(m - s))
            assert m == approx(s, abs = 1)
            print()

    def init(self, learn, sk, data):
        
        self.learn = learn
        self.sk = sk
        self.X_train, self.X_test, self.y_train, self.y_test = data
        self.learn_clf = self.learn.fit(self.X_train, self.y_train)
        self.sk_clf = self.sk.fit(self.X_train, self.y_train)

        self.learn_clf = learn.fit(self.X_train, self.y_train)
        self.sk_clf = sk.fit(self.X_train, self.y_train)

    def sklearn_compare(self, learn, sk, X_train, X_test, y_train, y_test):
        data = (X_train, X_test, y_train, y_test)
        self.init(learn, sk, data)

        

        attributes = ['intercept_', 'coef_']
        metrics = [r2_score, mean_squared_error]
        descriptions = ['r2:', 'MSE:']
        self.compare_performance(metrics, descriptions)
        print()
        self.compare_attributes(attributes)
        print("="*80)

    def test_reg(self, X, y, reg1, reg2):
        X_train, X_test, y_train, y_test = train_test_split(X,
                                                            y, 
                                                            test_size = 0.20, 
                                                            random_state = 0)
        self.sklearn_compare(reg1, reg2, X_train, X_test, y_train, y_test)
