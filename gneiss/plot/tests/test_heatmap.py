from gneiss.plot import heatmap
from gneiss.plot._heatmap import _sort_table

import pandas as pd
import pandas.util.testing as pdt
from skbio import TreeNode, DistanceMatrix
from scipy.cluster.hierarchy import ward
from gneiss.plot._dendrogram import SquareDendrogram
import numpy as np
import numpy.testing.utils as npt
import unittest


class HeatmapTest(unittest.TestCase):
    def setUp(self):
        np.random.seed(0)
        self.table = pd.DataFrame(np.random.random((5, 5)))
        num_otus = 5  # otus
        x = np.random.rand(num_otus)
        dm = DistanceMatrix.from_iterable(x, lambda x, y: np.abs(x-y))
        lm = ward(dm.condensed_form())
        t = TreeNode.from_linkage_matrix(lm, np.arange(len(x)).astype(np.str))
        self.t = SquareDendrogram.from_tree(t)
        self.md = pd.Series(['a', 'a', 'a', 'b', 'b'])
        for i, n in enumerate(t.postorder()):
            if not n.is_tip():
                n.name = "y%d" % i
            n.length = np.random.rand()*3

        self.highlights = pd.DataFrame({'y8': ['#FF0000', '#00FF00'],
                                        'y6': ['#0000FF', '#F0000F']}).T

    def test_sort_table(self):
        table = pd.DataFrame(
            [[1, 1, 0, 0, 0],
             [0, 1, 1, 0, 0],
             [0, 0, 1, 1, 0],
             [0, 0, 0, 1, 1]],
            columns=['s1', 's2', 's3', 's4', 's5'],
            index=['o1', 'o2', 'o3', 'o4'])
        mdvar = pd.Series(['a', 'b', 'a', 'b', 'a'],
                          index=['s1', 's2', 's3', 's4', 's5'])
        res_table, res_mdvar = _sort_table(table, mdvar)
        pdt.assert_index_equal(pd.Index(['s1', 's3', 's5', 's2', 's4']),
                               res_mdvar.index)
        pdt.assert_index_equal(pd.Index(['s1', 's3', 's5', 's2', 's4']),
                               res_table.columns)

    def test_basic(self):
        fig = heatmap(self.table, self.t, self.md)

        # Test to see if the lineages of the tree are ok
        lines = list(fig.get_axes()[1].get_lines())
        pts = self.t.coords(width=20, height=self.table.shape[0])
        pts['y'] = pts['y'] - 0.5  # account for offset
        pts['x'] = pts['x'].astype(np.float)
        pts['y'] = pts['y'].astype(np.float)

        npt.assert_allclose(lines[0]._xy,
                            pts.loc[['y5', '3'], ['x', 'y']])
        npt.assert_allclose(lines[1]._xy,
                            pts.loc[['y6', '0'], ['x', 'y']].values)
        npt.assert_allclose(lines[2]._xy,
                            pts.loc[['y7', '1'], ['x', 'y']].values)
        npt.assert_allclose(lines[3]._xy,
                            pts.loc[['y8', '2'], ['x', 'y']].values)
        npt.assert_allclose(lines[4]._xy,
                            pts.loc[['y5', '4'], ['x', 'y']].values)
        npt.assert_allclose(lines[5]._xy,
                            pts.loc[['y6', 'y5'], ['x', 'y']].values)
        npt.assert_allclose(lines[6]._xy,
                            pts.loc[['y7', 'y6'], ['x', 'y']].values)
        npt.assert_allclose(lines[7]._xy,
                            pts.loc[['y8', 'y7'], ['x', 'y']].values)

        # Make sure that the metadata labels are set properly
        res = str(fig.get_axes()[0].get_xticklabels(minor=True)[0])
        self.assertEqual(res, "Text(0,0,'a')")

        res = str(fig.get_axes()[0].get_xticklabels(minor=True)[1])
        self.assertEqual(res, "Text(0,0,'b')")

    def test_basic_highlights(self):
        fig = heatmap(self.table, self.t, self.md, self.highlights)

        # Test to see if the lineages of the tree are ok
        lines = list(fig.get_axes()[1].get_lines())
        pts = self.t.coords(width=20, height=self.table.shape[0])
        pts['y'] = pts['y'] - 0.5  # account for offset
        pts['x'] = pts['x'].astype(np.float)
        pts['y'] = pts['y'].astype(np.float)

        npt.assert_allclose(lines[0]._xy,
                            pts.loc[['y5', '3'], ['x', 'y']].values)
        npt.assert_allclose(lines[1]._xy,
                            pts.loc[['y6', '0'], ['x', 'y']].values)
        npt.assert_allclose(lines[2]._xy,
                            pts.loc[['y7', '1'], ['x', 'y']].values)
        npt.assert_allclose(lines[3]._xy,
                            pts.loc[['y8', '2'], ['x', 'y']].values)
        npt.assert_allclose(lines[4]._xy,
                            pts.loc[['y5', '4'], ['x', 'y']].values)
        npt.assert_allclose(lines[5]._xy,
                            pts.loc[['y6', 'y5'], ['x', 'y']].values)
        npt.assert_allclose(lines[6]._xy,
                            pts.loc[['y7', 'y6'], ['x', 'y']].values)
        npt.assert_allclose(lines[7]._xy,
                            pts.loc[['y8', 'y7'], ['x', 'y']].values)

        # Make sure that the metadata labels are set properly
        res = str(fig.get_axes()[0].get_xticklabels(minor=True)[0])
        self.assertEqual(res, "Text(0,0,'a')")

        res = str(fig.get_axes()[0].get_xticklabels(minor=True)[1])
        self.assertEqual(res, "Text(0,0,'b')")

        # Make sure that the highlight labels are set properly
        res = str(fig.get_axes()[2].get_xticklabels()[0])
        self.assertEqual(res, "Text(0,0,'y6')")

        res = str(fig.get_axes()[2].get_xticklabels()[1])
        self.assertEqual(res, "Text(0,0,'y8')")


if __name__ == "__main__":
    unittest.main()
