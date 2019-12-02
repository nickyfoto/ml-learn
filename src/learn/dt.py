import numpy as np
from scipy.stats import pearsonr
from collections import Counter  
from sklearn.base import BaseEstimator
from math import log2

def get_pearsonr(feature, Y):
    return abs(pearsonr(feature, Y)[0])

def entropy(class_y):

    res = 0
    c = Counter(class_y)
    m = len(class_y)
    for k, v in c.items():
        res -= (v/m) * log2(v/m)
    return res

def _information_gain(current_y, y_entropy):

    current_y_length = current_y[0].shape[0] + current_y[1].shape[0]
    # current_entropy = sum([entropy(c) * len(c) / current_y_length for c in current_y])
    c0 = entropy(current_y[0]) * current_y[0].shape[0] / current_y_length
    c1 = entropy(current_y[1]) * current_y[1].shape[0] / current_y_length
    return y_entropy - c0 - c1

def _partition_classes(X, y, split_attribute, split_val):

    left_indices = X[:,split_attribute] <= split_val
    X_left = X[left_indices]
    y_left = y[left_indices]
    X_right = X[~left_indices]
    y_right = y[~left_indices]
    return X_left, X_right, y_left, y_right

def _find_best_split(X, y, split_attribute, y_entropy):
    
    vals = [x[split_attribute] for x in X]
    unique_vals = np.unique(vals)
    info_gains = []
    for i in range(len(unique_vals)):
        _, _, y_left, y_right = _partition_classes(X, y, split_attribute, unique_vals[i])
        current_y = [y_left, y_right]
        info_gains.append(_information_gain(current_y, y_entropy))
    # print(info_gains)
    max_idx = np.argmax(info_gains)
    return unique_vals[max_idx], info_gains[max_idx]


def _find_best_feature(X, y):
    
    info_gains = []
    split_vals = []
    split_attributes = range(X[0].shape[0])
    y_entropy = entropy(y)


    column_equality = np.all(X == X[0,:], axis = 0)

    for split_attribute, all_equal_column in zip(split_attributes, column_equality):
        if all_equal_column:
            info_gains.append(0.0)
            split_vals.append(X[:,split_attribute][0])
            # print('skipping all all_equal_column')
        else:
            split_val, info_gain = _find_best_split(X, y, split_attribute, y_entropy=y_entropy)
            info_gains.append(info_gain)
            split_vals.append(split_val)
    # print(info_gains)
    max_idx = np.argmax(info_gains)
    return split_attributes[max_idx], split_vals[max_idx]


class DecisionTree(BaseEstimator):
                                                                
    def __init__(self, 
                    verbose = False,
                    criterion = 'pearsonr',
                    leaf_size = 1,
                    max_depth = None,
                    ):   
        self.leaf_size = 1
        self.tree = None
        self.criterion = criterion
        self.max_depth = max_depth

    def _get_criterion_score(self, dataX, dataY, split_func):
        n_features= dataX.shape[1]
        # if feature i have the same value in all dataX
        # return (0, i)
        return sorted([(0, i) if (dataX[:,i][0] == dataX[:,i]).all() else 
                        # (abs(pearsonr(dataX[:, i], dataY)[0]), i) 
                        (split_func(dataX[:, i], dataY), i) 
                        for i in range(n_features)])

    def _cannot_split(self, dataY):
        n_train = np.array(dataY).shape[0]
        return (n_train <= self.leaf_size or len(np.unique(dataY)) == 1)

    def splited(self, left_index):
        """
        successfully splited
        """
        return len(np.unique(left_index)) > 1
        
    def _build_tree(self, dataX, dataY, depth):
        """Builds the Decision Tree recursively by choosing the best feature to split on and 
        the splitting value. The best feature has the highest absolute correlation with dataY. 
        If all features have the same absolute correlation, choose the first feature. The 
        splitting value is the median of the data according to the best feature. 
        If the best feature doesn't split the data into two groups, choose the second best 
        one and so on; if none of the features does, return leaf
        Parameters:
        dataX: A numpy ndarray of X values at each node
        dataY: A numpy 1D array of Y values at each node
        
        Returns:
        tree: A numpy ndarray. Each row represents a node and four columns are feature indices 
        (int type; index for a leaf is -1), splitting values, and starting rows, from the current 
        root, for its left and right subtrees (if any)
        """
        # print(np.array(dataX).shape, np.array(dataY).shape, 'depth=', depth)
        if self.max_depth and depth >= self.max_depth:
            leaf_node = np.array([[-1, Counter(dataY).most_common(1)[0][0], np.nan, np.nan]])
            return leaf_node

        if self._cannot_split(dataY):
            # Leaf value is the most common dataY
            leaf_node = np.array([[-1, Counter(dataY).most_common(1)[0][0], np.nan, np.nan]])
            return leaf_node

        if self.criterion == 'pearsonr':
            feature_corrs = self._get_criterion_score(dataX, dataY, get_pearsonr)
            while feature_corrs:
                feature_to_split = feature_corrs.pop()[1]
                split_val = np.median(dataX[:, feature_to_split])
                left_index = dataX[:, feature_to_split] <= split_val
                right_index = dataX[:, feature_to_split] > split_val
                if self.splited(left_index):
                    break
            if not feature_corrs:
                leaf_node = np.array([[-1, Counter(dataY).most_common(1)[0][0], np.nan, np.nan]])
                return leaf_node
            
            left_tree = self._build_tree(dataX[left_index], dataY[left_index], depth)
            right_tree = self._build_tree(dataX[right_index], dataY[right_index], depth)    
            root = np.array([[feature_to_split, split_val, 1, left_tree.shape[0] + 1]])
            res = np.vstack((root, left_tree, right_tree))
            return res
        else:
            feature_to_split, split_val = _find_best_feature(dataX, dataY)
            X_left, X_right, y_left, y_right = _partition_classes(dataX, dataY, 
                                                feature_to_split, split_val)
            depth += 1
            left_tree = self._build_tree(X_left, y_left, depth)
            right_tree = self._build_tree(X_right, y_right, depth)    
            root = np.array([[feature_to_split, split_val, 1, left_tree.shape[0] + 1]])
            res = np.vstack((root, left_tree, right_tree))#.astype(root.dtype)
            # print(res.dtype)
            # print(root.dtype, left_tree.dtype, right_tree.dtype, res.dtype)
            return res


    def _search_point(self, point, row):
        """A private function to be used with query. It recursively searches 
        the decision tree matrix and returns a predicted value for point.
        Parameters:
        point: A numpy 1D array of test query
        row: The row of the decision tree matrix to search
    
        Returns 
        pred: The predicted value
        """
        loc, split_val = self.tree[row, :2]
        if loc == -1:
            return split_val
        elif point[int(loc)] <= split_val:
            pred = self._search_point(point, row + int(self.tree[row, 2]))
        else:
            pred = self._search_point(point, row + int(self.tree[row, 3]))
        return pred

    def fit(self, dataX, dataY):
        # print(dataY.shape)
        new_tree = self._build_tree(dataX, dataY, depth=0)
        if not self.tree:
            self.tree = new_tree
        else:
            self.tree = np.vstack((self.tree, new_tree))
        return self

    def predict(self, points):
        """Estimates a set of test points given the model we built
        
        Parameters:
        points: A numpy ndarray of test queries
        Returns: 
        preds: A numpy 1D array of the estimated values
        """                                                         
        preds = [self._search_point(point, row=0) for point in points]
        return preds



class DecisionTreeD(BaseEstimator):
    def __init__(self,
                    leaf_size = 1,
                    max_depth = None,
                    verbose=False):
        self.max_depth = max_depth
        self.leaf_size = leaf_size
        self.leaves = []
        self.verbose = verbose
    def _cannot_split(self, y):
        n_examples = np.array(y).shape[0]
        return (n_examples <= self.leaf_size or len(np.unique(y)) == 1)

    def _get_val(self, c0, c1, node):
        if c0 >= c1:
            node['val'] = 0
        else:
            node['val'] = 1

    def get_leaf_node(self, y, parent):
        c = Counter(y)
        if c[0] >= c[1]:
            leaf_node = {'is_leaf': True, 'val': 0, 'parent': parent}
        else:
            leaf_node = {'is_leaf': True, 'val': 1, 'parent': parent}
        self.leaves.append(leaf_node)
        return c[0], c[1], leaf_node


    def _build_tree(self, X, y, parent, depth=0):
        if self.verbose:
            print(np.array(X).shape, np.array(y).shape, 'depth=', depth)
        if self.max_depth and depth >= self.max_depth:
            return self.get_leaf_node(y, parent)            
            
        if self._cannot_split(y):
            return self.get_leaf_node(y, parent)

        feature_to_split, split_val = _find_best_feature(X, y)
        X_left, X_right, y_left, y_right = _partition_classes(X, y, 
                                                feature_to_split, split_val)
        node = {'is_leaf': False}
        node['feature_to_split'] = feature_to_split
        node['split_val'] = split_val
        depth += 1
        # node['depth'] = depth
        if parent:
            node['parent'] = parent
        l0, l1, node['left'] = self._build_tree(X_left, y_left, 
                                                    parent=node,
                                                    depth=depth)
        r0, r1, node['right'] = self._build_tree(X_right, y_right, 
                                                    parent=node,
                                                    depth=depth)
        self._get_val(l0+r0, l1+r1, node)
        return l0+r0, l1+r1, node

    def fit(self, X, y):
        self.tree = {}
        c0, c1, self.tree['root'] = self._build_tree(
                                                    X,
                                                    y, 
                                                    parent=None,
                                                    depth=0)
        self._get_val(c0, c1, self.tree['root'])
        return self

    def _search_point(self, point, tree):
        if tree['is_leaf']:
            return tree['val']
        else:
            if point[tree['feature_to_split']] <= tree['split_val']:
                return self._search_point(point, tree['left'])
            else:
                return self._search_point(point, tree['right'])

    def bunch_predict(self, X):                                                        
        preds = [self._search_point(point, self.tree['root']) for point in X]
        return preds

    def predict(self, record):
        """
        TODO: classify a sample in test data set using self.tree and return the predicted label
        """
        #  Delete this line when you implement the function
        # raise NotImplementedError
        return self._search_point(record, self.tree['root'])