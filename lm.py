import numpy as np

from sklearn.base import BaseEstimator

class LinearRegression(BaseEstimator):
    
    def __init__(self, fit_intercept=True):
        self.weights = None
        self.fit_intercept = fit_intercept

    def _fit_intercept(self, X):
        intercept = np.ones((X.shape[0], 1))
        return np.hstack((intercept, X))

    def fit(self, X, y):
        """
        Args:
            X: mxn numpy array
            y: (m,)
        Return:
            self
        """
        self.m, self.n = X.shape
        if self.fit_intercept:
            X = self._fit_intercept(X)
        self.weights = np.linalg.inv(X.T.dot(X)).dot(X.T).dot(y)
        return self

    @property
    def intercept_(self):
        return self.weights[0]

    @property
    def coef_(self):
        if self.n == 1:
            return self.weights[1:]
        return self.weights[1:]

    def predict(self, X):
        if self.fit_intercept:
            X = self._fit_intercept(X)
        return np.dot(X, self.weights)



class SGDRegressor(BaseEstimator):

    def __init__(self, fit_intercept=True, max_iter=1000,
                    learning_rate=0.001,
                    penalty=None,
                    alpha=0):

        self.weights = None
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.learning_rate = learning_rate
        self.penalty = penalty
        self.alpha = alpha

    def _fit_intercept(self, X):
        intercept = np.ones((X.shape[0], 1))
        return np.hstack((intercept, X))

    def fit(self, X, y):
        if self.fit_intercept:
            X = self._fit_intercept(X)
        
        self.m, self.n = X.shape
        self.weights = np.zeros((self.n, 1))
        for i in range(self.max_iter):
            for j in range(self.m):
                pred = np.dot(X[j], self.weights)
                error = pred - y[j]
                if self.penalty:
                    gradient = (error * X[[j]]).T
                    self.weights[0] -= self.learning_rate * gradient[0]
                    self.weights[1:] -= self.learning_rate * (gradient[1:] +  
                                                            self.alpha * self.weights[1:] / self.m)
                else:
                    gradient = error * X[[j]]
                    self.weights -= self.learning_rate*gradient.T
        return self
    
    @property
    def intercept_(self):
        return self.weights[:1].flatten()

    @property
    def coef_(self):
        if self.n == 1:
            return self.weights[1:]
        return self.weights[1:].flatten()

    def predict(self, X):
        if self.fit_intercept:
            X = self._fit_intercept(X)
        return np.dot(X, self.weights)


class Ridge(BaseEstimator):
    """
    Note:
        No equivalent Normal Equation solver in sklearn Ridge implementation
    """
    def __init__(self, fit_intercept=True, alpha=1.0):
        self.weights = None
        self.fit_intercept = fit_intercept
        self.c_lambda = alpha

    def _fit_intercept(self, X):
        intercept = np.ones((X.shape[0], 1))
        return np.hstack((intercept, X))

    def fit(self, X, y):
        if self.fit_intercept:
            X = self._fit_intercept(X)
        self.m, self.n = X.shape
        
        L = np.eye(self.n)
        L[0,0] = 0
        self.c_lambda *= L
        self.weights = np.linalg.inv(X.T.dot(X) + self.c_lambda).dot(X.T).dot(y)
        return self

    @property
    def coef_(self):
        if self.n == 1:
            return self.weights[1:]
        return self.weights[1:]

    def predict(self, X):
        if self.fit_intercept:
            X = self._fit_intercept(X)
        return np.dot(X, self.weights)


if __name__ == '__main__':
    
    from time import time

    from sklearn import datasets
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn import linear_model
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split

    from evaluation import TestSK

    def sklearn_compare(learn, sk, X_train, X_test, y_train, y_test):
        data = (X_train, X_test, y_train, y_test)
        ts = TestSK(learn=learn,
                                sk=sk, 
                                data=data)

        attributes = ['intercept_', 'coef_']
        metrics = [r2_score, mean_squared_error]
        descriptions = ['r2:', 'MSE:']
        ts.compare_performance(metrics, descriptions)
        print()
        ts.compare_attributes(attributes)
        print("="*80)

    def test_reg(X, y, reg1, reg2):
        X_train, X_test, y_train, y_test = train_test_split(X,
                                                            y, 
                                                            test_size = 0.20, 
                                                            random_state = 0)
        sklearn_compare(reg1, reg2, X_train, X_test, y_train, y_test)


    # test command
    # python3 lm.py > test_reports/reg.txt
    start = time()
    print("Start testing")

    boston = datasets.load_boston()
    X = boston.data
    y = boston.target
    
    # SGD is sensitive to feature scale 
    # so standarize X before training



    reg = LinearRegression()
    skreg = linear_model.LinearRegression()

    print('Testing Standardized boston dataset')

    #test_reg(X, y, reg, skreg)

    scaler = StandardScaler()
    X = scaler.fit_transform(X) 

    #test_reg(X, y, sgd, sksgd)


    sgd_r = SGDRegressor(penalty='l2', alpha=1e2, max_iter=2000)
    sksgd_r = linear_model.SGDRegressor(random_state=0, verbose=1, shuffle=False)
    test_reg(X, y, sgd_r, sksgd_r)

    print('Testing 1D diabetes')
    diabetes = datasets.load_diabetes()
    # Use only one feature
    X = diabetes.data[:, np.newaxis, 2]
    y = diabetes.target
    # test_reg(X, y, reg, skreg)


    scaler = StandardScaler()
    X = scaler.fit_transform(X) 

    # test_reg(X, y, sgd, sksgd)

    # Testing SGD with l2 regularization
    
    

    print('End testing')
    end = time()
    print(end - start)

    # def f(x):
    #     return x * np.sin(x)
    # x = np.linspace(0, 10, 100)
    # rng = np.random.RandomState(0)
    # rng.shuffle(x)
    # x = np.sort(x[:20])
    # y = f(x)

    # # create matrix versions of these arrays
    # X = x[:, np.newaxis]
    # # print(X.shape)
    # reg = Ridge()
    # reg.fit(X, y)
    # print(reg.predict(X))