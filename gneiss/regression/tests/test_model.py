# ----------------------------------------------------------------------------
# Copyright (c) 2016--, gneiss development team.
#
# Distributed under the terms of the GPLv3 License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------
import pandas as pd
from skbio import TreeNode
from skbio.stats.composition import ilr_inv
import numpy as np
import statsmodels.formula.api as smf
import pandas.util.testing as pdt
from gneiss.regression._model import RegressionModel
from gneiss.balances import balance_basis
import unittest
import os


# create some mock classes for testing
class submock(RegressionModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def summary(self):
        print("OK!")


class TestRegressionModel(unittest.TestCase):
    def setUp(self):
        self.pickle_fname = "test.pickle"
        self.data = pd.DataFrame([[1, 1, 1],
                                  [3, 2, 3],
                                  [4, 3, 2],
                                  [5, 4, 4],
                                  [2, 5, 3],
                                  [3, 6, 5],
                                  [4, 7, 4]],
                                 index=['s1', 's2', 's3', 's4',
                                        's5', 's6', 's7'],
                                 columns=['Y1', 'Y2', 'X'])
        self.model1 = smf.ols(formula="Y1 ~ X", data=self.data)
        self.model2 = smf.ols(formula="Y2 ~ X", data=self.data)
        self.tree = TreeNode.read(['((a,b)Y1, c)Y2;'])
        self.basis = pd.DataFrame(balance_basis(self.tree)[0],
                                  columns=['a', 'b', 'c'], index=['Y1', 'Y2'])
        self.balances = pd.DataFrame(self.data[['Y1', 'Y2']],
                                     index=self.data.index, columns=['Y1', 'Y2'])

    def tearDown(self):
        if os.path.exists(self.pickle_fname):
            os.remove(self.pickle_fname)

    def test_regression_results_pvalues(self):
        # checks to see if pvalues are calculated correctly.

        submodels = [self.model1, self.model2]
        res = submock(submodels=submodels, basis=self.basis,
                      tree=self.tree, balances=self.balances)
        res.fit()
        exp = pd.DataFrame({'Intercept': [0.307081, 0.972395],
                            'X': [0.211391, 0.029677]},
                           index=['Y1', 'Y2'])
        pdt.assert_frame_equal(res.pvalues, exp,
                               check_exact=False,
                               check_less_precise=True)

    def test_check_projection(self):
        feature_names = ['Z1', 'Z2', 'Z3']
        basis = _gram_schmidt_basis(3)
        submodels = [self.model1, self.model2]
        res = RegressionResults(submodels=submodels, basis=self.basis,
                                tree=self.tree, balances=self.balances)

        feature_names = ['Z1', 'Z2', 'Z3']
        basis = _gram_schmidt_basis(3)

        # Test if feature_names is checked for
        res = RegressionResults(self.results, basis=basis)
        with self.assertRaises(ValueError):
            res._check_projection(True)

        # Test if basis is checked for
        res = RegressionResults(self.results, feature_names=feature_names)
        with self.assertRaises(ValueError):
            res._check_projection(True)

    def test_regression_results_coefficient(self):
        exp_coef = pd.DataFrame({'Intercept': [1.447368, -0.052632],
                                 'X': [0.539474, 1.289474]},
                                index=['Y1', 'Y2'])

        res = RegressionResults(submodels=submodels, basis=self.basis,
                                tree=self.tree, balances=self.balances)

        pdt.assert_frame_equal(res.coefficients(), exp_coef,
                               check_exact=False,
                               check_less_precise=True)

    def test_regression_results_coefficient_projection(self):
        exp_coef = pd.DataFrame(
            {'Intercept': ilr_inv(np.array([[1.447368, -0.052632]])),
             'X': ilr_inv(np.array([[0.539474, 1.289474]]))},
            index=['Z1', 'Z2', 'Z3'])
        feature_names = ['Z1', 'Z2', 'Z3']
        basis = _gram_schmidt_basis(3)

        res = RegressionResults(submodels=submodels, basis=self.basis,
                                tree=self.tree, balances=self.balances)



        pdt.assert_frame_equal(res.coefficients(project=True), exp_coef,
                               check_exact=False,
                               check_less_precise=True)

    def test_regression_results_coefficient_project_error(self):
        res = RegressionResults(self.results)
        with self.assertRaises(ValueError):
            res.coefficients(project=True)

    def test_regression_results_residuals_projection(self):
        A = np.array  # aliasing np.array for the sake of pep8
        exp_resid = pd.DataFrame({'s1': ilr_inv(A([-0.986842, -0.236842])),
                                  's2': ilr_inv(A([-0.065789, -1.815789])),
                                  's3': ilr_inv(A([1.473684, 0.473684])),
                                  's4': ilr_inv(A([1.394737, -1.105263])),
                                  's5': ilr_inv(A([-1.065789, 1.184211])),
                                  's6': ilr_inv(A([-1.144737, -0.394737])),
                                  's7': ilr_inv(A([0.394737, 1.894737]))},
                                 index=['Z1', 'Z2', 'Z3']).T
        feature_names = ['Z1', 'Z2', 'Z3']
        basis = _gram_schmidt_basis(3)
        res = RegressionResults(self.results, basis=basis,
                                feature_names=feature_names)
        pdt.assert_frame_equal(res.residuals(project=True), exp_resid,
                               check_exact=False,
                               check_less_precise=True)

    def test_regression_results_residuals(self):
        exp_resid = pd.DataFrame({'s1': [-0.986842, -0.236842],
                                  's2': [-0.065789, -1.815789],
                                  's3': [1.473684, 0.473684],
                                  's4': [1.394737, -1.105263],
                                  's5': [-1.065789, 1.184211],
                                  's6': [-1.144737, -0.394737],
                                  's7': [0.394737, 1.894737]},
                                 index=['Y1', 'Y2']).T
        res = RegressionResults(self.results)
        pdt.assert_frame_equal(res.residuals(), exp_resid,
                               check_exact=False,
                               check_less_precise=True)

    def test_regression_results_predict(self):
        model = RegressionResults(self.results)
        res_predict = model.predict(self.data[['X']])

        exp_predict = pd.DataFrame({'s1': [1.986842, 1.236842],
                                    's2': [3.065789, 3.815789],
                                    's3': [2.526316, 2.526316],
                                    's4': [3.605263, 5.105263],
                                    's5': [3.065789, 3.815789],
                                    's6': [4.144737, 6.394737],
                                    's7': [3.605263, 5.105263]},
                                   index=['Y1', 'Y2']).T

        pdt.assert_frame_equal(res_predict, exp_predict)

    def test_regression_results_predict_extrapolate(self):
        model = RegressionResults(self.results)
        extrapolate = pd.DataFrame({'X': [8, 9, 10]},
                                   index=['k1', 'k2', 'k3'])
        res_predict = model.predict(extrapolate)

        exp_predict = pd.DataFrame({'k1': [5.76315789, 10.26315789],
                                    'k2': [6.30263158, 11.55263158],
                                    'k3': [6.84210526, 12.84210526]},
                                   index=['Y1', 'Y2']).T

        pdt.assert_frame_equal(res_predict, exp_predict)

    def test_regression_results_predict_projection(self):
        feature_names = ['Z1', 'Z2', 'Z3']
        basis = _gram_schmidt_basis(3)
        model = RegressionResults(self.results, basis=basis,
                                  feature_names=feature_names)

        res_predict = model.predict(self.data[['X']], project=True)
        A = np.array  # aliasing np.array for the sake of pep8
        exp_predict = pd.DataFrame({'s1': ilr_inv(A([1.986842, 1.236842])),
                                    's2': ilr_inv(A([3.065789, 3.815789])),
                                    's3': ilr_inv(A([2.526316, 2.526316])),
                                    's4': ilr_inv(A([3.605263, 5.105263])),
                                    's5': ilr_inv(A([3.065789, 3.815789])),
                                    's6': ilr_inv(A([4.144737, 6.394737])),
                                    's7': ilr_inv(A([3.605263, 5.105263]))},
                                   index=feature_names).T

        pdt.assert_frame_equal(res_predict, exp_predict)

    def test_regression_results_predict_none(self):
        submodels = [self.model1, self.model2]
        model = RegressionResults(submodels=submodels, basis=self.basis,
                                  tree=self.tree, balances=self.balances)
        res_predict = model.predict()

        exp_predict = pd.DataFrame({'s1': [1.986842, 1.236842],
                                    's2': [3.065789, 3.815789],
                                    's3': [2.526316, 2.526316],
                                    's4': [3.605263, 5.105263],
                                    's5': [3.065789, 3.815789],
                                    's6': [4.144737, 6.394737],
                                    's7': [3.605263, 5.105263]},
                                   index=['Y1', 'Y2']).T

        pdt.assert_frame_equal(res_predict, exp_predict)


if __name__ == "__main__":
    unittest.main()
