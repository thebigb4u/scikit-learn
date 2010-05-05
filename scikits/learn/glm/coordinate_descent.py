# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

# $Id$
"""Implementation of regularized linear regression with Coordinate Descent

This implementation is focused on regularizers that lead to sparse parameters
(many zeros) such as the laplacian (L1) and Elastic Net (L1 + L2) priors:

  http://en.wikipedia.org/wiki/Generalized_linear_model

The objective function to minimize is for the Lasso::

        0.5 * ||R||_2 ^ 2 + alpha * ||w||_1

and for the Elastic Network::

        0.5 * ||R||_2 ^ 2 + alpha * ||w||_1 + beta * 0.5 * ||w||_2 ^ 2

Where R are the residuals between the output of the model and the expected
value and w is the vector of weights to fit.
"""

import numpy as np
import scipy.linalg as linalg
from cd_fast import lasso_coordinate_descent, enet_coordinate_descent
from utils import lasso_objective, enet_objective, density

class LinearModel(object):
    """Base class for Linear Model optimized with coordinate descent"""

    def __init__(self, w0=None):
        # weights of the model (can be lazily initialized by the ``fit`` method)
        self.coef_ = w0

    def predict(self, X):
        """Linear model prediction: compute the dot product with the weights"""
        X = np.asanyarray(X)
        return np.dot(X, self.coef_)

    def compute_density(self):
        """Ratio of non-zero weights in the model"""
        return density(self.coef_)


class Lasso(LinearModel):
    """Linear Model trained with L1 prior as regularizer (a.k.a. the Lasso)"""

    def __init__(self, alpha=1.0, w0=None):
        super(Lasso, self).__init__(w0)
        self.alpha = float(alpha)

    def fit(self, X, Y, maxit=100, tol=1e-4):
        """Fit Lasso model with coordinate descent"""
        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)
            
        self.coef_, self.dual_gap_ = \
                    lasso_coordinate_descent(self.coef_, self.alpha, X, Y, maxit, 10, tol)

        # return self for chaining fit and predict calls
        return self

    
    def __repr__(self):
        return "Lasso cd"


class ElasticNet(LinearModel):
    """Linear Model trained with L1 and L2 prior as regularizer"""

    def __init__(self, alpha=1.0, beta=1.0, w0=None):
        super(ElasticNet, self).__init__(w0)
        self.alpha = alpha
        self.beta = beta

    def fit(self, X, Y, maxit=100, tol=1e-4):
        """Fit Elastic Net model with coordinate descent"""
        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)
            
        self.coef_, self.dual_gap_ = \
                    enet_coordinate_descent(self.coef_, self.alpha, self.beta, X, Y, maxit, 10, tol)

        # return self for chaining fit and predict calls
        return self

    def __repr__(self):
        return "ElasticNet cd"


def lasso_path(X, y, factor=0.95, n_alphas = 10, **kwargs):
    """Compute Lasso path with coordinate descent"""
    alpha_max = np.abs(np.dot(X.T, y)).max()
    alpha = alpha_max
    model = Lasso(alpha=alpha)
    weights = []
    alphas = np.empty(0)
    for _ in range(n_alphas):
        # warm restarts
        model.alpha *= factor
        model.fit(X, y, **kwargs)

        alphas = np.append(alphas, model.alpha)
        weights.append(model.coef_.copy())

        alphas = np.asarray(alphas)
    weights = np.asarray(weights)
    return alphas, weights

def enet_path(X, y, factor=0.95, n_alphas=10, beta=1.0, **kwargs):
    """Compute Elastic-Net path with coordinate descent"""
    alpha_max = np.abs(np.dot(X.T, y)).max()
    alpha = alpha_max
    model = ElasticNet(alpha=alpha, beta=beta)
    weights = []
    alphas = []
    for _ in range(n_alphas):
        model.alpha *= factor
        model.fit(X, y, **kwargs)

        alphas.append(model.alpha)
        weights.append(model.w.copy())

    alphas = np.asarray(alphas)
    weights = np.asarray(weights)
    return alphas, weights