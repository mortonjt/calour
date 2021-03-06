# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from unittest import main

from skbio.util import get_data_path

from calour._testing import Tests, assert_experiment_equal
import calour as ca


class FilteringTests(Tests):
    def setUp(self):
        super().setUp()
        self.test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat, normalize=None)
        self.test1 = ca.read(self.test1_biom, self.test1_samp, self.test1_feat, normalize=None)

    def test_downsample_sample(self):
        obs = self.test2.downsample('group')
        # should be down to 4 samples; feature number is the same
        self.assertEqual(obs.shape, (4, 8))

        sid = obs.sample_metadata.index.tolist()
        all_sid = self.test2.sample_metadata.index.tolist()
        exp = self.test2.reorder([all_sid.index(i) for i in sid])
        assert_experiment_equal(obs, exp)

    def test_downsample_feature(self):
        obs = self.test2.downsample('oxygen', axis=1)
        sid = obs.feature_metadata.index.tolist()
        self.assertEqual(obs.shape, (9, 4))

        all_sid = self.test2.feature_metadata.index.tolist()
        exp = self.test2.reorder([all_sid.index(i) for i in sid], axis=1)
        self.assertEqual(obs, exp)

    def test_downsample_num_keep_too_big(self):
        # test error raised when num_keep is too big
        with self.assertRaises(ValueError):
            self.test2.downsample('group', num_keep=9)

    def test_downsample_num_keep(self):
        # test keeping num_keep samples, and inplace
        obs = self.test1.downsample('group', num_keep=9, inplace=True)
        # should be down to 2 groups (18 samples); feature number is the same
        self.assertEqual(obs.shape, (18, 12))
        self.assertEqual(set(obs.sample_metadata['group']), set(['1', '2']))
        self.assertIs(obs, self.test1)

    def test_filter_by_metadata_sample_edge_cases(self):
        # no group 3 - none filtered
        obs = self.test2.filter_by_metadata('group', [3])
        self.assertEqual(obs.shape, (0, 8))
        obs = self.test2.filter_by_metadata('group', [3], negate=True)
        assert_experiment_equal(obs, self.test2)

        # all samples are filtered
        obs = self.test2.filter_by_metadata('group', [1, 2])
        assert_experiment_equal(obs, self.test2)
        obs = self.test2.filter_by_metadata('group', [1, 2], negate=True)
        self.assertEqual(obs.shape, (0, 8))

    def test_filter_by_metadata_sample(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat,
                            sparse=sparse, normalize=None)
            # only filter samples bewtween 3 and 7.
            obs = test2.filter_by_metadata(
                'ori.order', lambda l: [7 > i > 3 for i in l], inplace=inplace)
            self.assertEqual(obs.shape, (3, 8))
            self.assertEqual(obs.sample_metadata.index.tolist(),
                             ['S5', 'S6', 'S7'])
            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_metadata_feature_edge_cases(self):
        # none filtered
        obs = self.test2.filter_by_metadata('oxygen', ['facultative'], axis=1)
        self.assertEqual(obs.shape, (9, 0))
        obs = self.test2.filter_by_metadata('oxygen', ['facultative'], axis=1, negate=True)
        assert_experiment_equal(obs, self.test2)

    def test_filter_by_metadata_feature(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat,
                            sparse=sparse, normalize=None)
            # only filter samples with id bewtween 3 and 7.
            obs = test2.filter_by_metadata(
                'oxygen', ['anaerobic'], axis=1, inplace=inplace)
            self.assertEqual(obs.shape, (9, 2))
            self.assertEqual(
                obs.feature_metadata.index.tolist(),
                ['TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTA'
                 'GGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGC'
                 'CTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                 'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTA'
                 'GGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTG'
                 'CAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG'])
            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_data_sample_edge_cases(self):
        # all samples are filtered out
        obs = self.test2.filter_by_data('sum_abundance', cutoff=100000)
        self.assertEqual(obs.shape, (0, 8))
        # none is filtered out
        obs = self.test2.filter_by_data('sum_abundance', cutoff=1)
        assert_experiment_equal(obs, self.test2)
        self.assertIsNot(obs, self.test2)

    def test_filter_by_data_sample(self):
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            test2 = ca.read(self.test2_biom, self.test2_samp, self.test2_feat,
                            sparse=sparse, normalize=None)
            # filter out samples with abundance < 1200. only the last sample is filtered out.
            obs = test2.filter_by_data(
                'sum_abundance', axis=0, inplace=inplace, cutoff=1200)
            self.assertEqual(obs.shape, (8, 8))
            exp = ca.read(*[get_data_path(i) for i in [
                'test2.biom.filter.sample',
                'test2.sample',
                'test2.feature']],
                          normalize=None)
            assert_experiment_equal(obs, exp)
            if inplace:
                self.assertIs(obs, test2)
            else:
                self.assertIsNot(obs, test2)

    def test_filter_by_data_feature_edge_cases(self):
        # all features are filtered out
        obs = self.test2.filter_by_data('sum_abundance', axis=1, cutoff=10000)
        self.assertEqual(obs.shape, (9, 0))

        # none is filtered out
        obs = self.test2.filter_by_data('sum_abundance', axis=1, cutoff=1)
        assert_experiment_equal(obs, self.test2)
        self.assertIsNot(obs, self.test2)

    def test_filter_by_data_feature(self):
        # one feature is filtered out when cutoff is set to 25
        for sparse, inplace in [(True, False), (True, True), (False, False), (False, True)]:
            obs = self.test2.filter_by_data(
                'sum_abundance', axis=1, inplace=inplace, cutoff=25)
            self.assertEqual(obs.shape, (9, 7))
            exp = ca.read(*[get_data_path(i) for i in [
                'test2.biom.filter.feature',
                'test2.sample',
                'test2.feature']],
                          normalize=None)
            assert_experiment_equal(obs, exp)
            if inplace:
                self.assertIs(obs, self.test2)
            else:
                self.assertIsNot(obs, self.test2)

    def test_filter_min_abundance(self):
        exp = self.test1.filter_min_abundance(17008)
        self.assertEqual(exp.shape[1], 2)
        okseqs = ['TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTAGGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGCCTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTGCAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG']
        self.assertCountEqual(exp.feature_metadata.index, okseqs)

    def test_filter_prevalence(self):
        # default value is 0.5 - keep only features present at least in 0.5 the samples
        exp = self.test1.filter_prevalence()
        okseqs = ['TACGTATGTCACAAGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCCGTGGATTAAGCGTGTTGTGAAATGTAGACGCTCAACGTCTGAATCGCAGCGCGAACTGGTTCACTTGAGTATGCACAACGTAGGCGGAATTCGTCG',
                  'TACATAGGTCGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGTTCGTAGGCTGTTTATTAAGTCTGGAGTCAAATCCCAGGGCTCAACCCTGGCTCGCTTTGGATACTGGTAAACTAGAGTTAGATAGAGGTAAGCAGAATTCCATGT',
                  'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTTTGTAAGTCTGATGTGAAATCCCCGGGCTCAACCTGGGAATTGCATTGGAGACTGCAAGGCTAGAATCTGGCAGAGGGGGGTAGAATTCCACG',
                  'TACGTAGGTGGCAAGCTTTGTCCTTCCTTATTTGGCGTAAAGCGCGCGCAGGCGGCCTATCCAGTCTGTCTTAAAAGTTCGGGGCTCAACCCCGTGATGGGATGGAAACTAGTAGGCTAGAGTATCGGAGAGGAAAGCGGAATTCCTAGT',
                  'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTAGGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTGCCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG',
                  'TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTAGGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTGCGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTAGGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGCCTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTGCAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG']
        self.assertCountEqual(exp.feature_metadata.index, okseqs)
        self.assertEqual(exp.shape[1], 8)
        self.assertEqual(exp.shape[0], self.test1.shape[0])

    def test_filter_mean(self):
        # default is 0.01 - keep features with mean abundance >= 1%
        exp = self.test1.filter_mean()
        okseqs = ['TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTAGGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTGCGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTAGGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGCCTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTGCAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG']
        self.assertCountEqual(exp.feature_metadata.index, okseqs)
        self.assertEqual(exp.shape[1], 3)
        self.assertEqual(exp.shape[0], self.test1.shape[0])

    def test_filter_ids_default(self):
        okseqs = ['TACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCTTGTAGGCGGTTGGTCGCGTCTGCCGTGAAATTCTCTGGCTTAACTGGAGGCGTGCGGTGGGTACGGGCTGACTTGAGTGCGGTAGGGGAGACTGGAACTCCTGG',
                  'TACGTAGGGCGCGAGCGTTATCCGGAATTATTGGGCGTAAAGAGTGCGTAGGTGGCATCTTAAGCGCAGGGTTTAAGGCAATGGCTCAACCATTGTTCGCCTTGCGAACTGGGGTGCTTGAGTGCAGGAGGGGAAAGTGGAATTCCTAGT',
                  'AAAAAAAGGTCCAGGCGTTATCCGGATTTATTGGGTTTAAAGGGAGCGTAGGCGGACGATTAAGTCAGCTGCGAAAGTTTGCGGCTCAACCGTAAAATTGCAGTTGAAACTGGTTGTCTTGAGTGCACGCAGGGATGTTGGAATTCATGG',
                  'pita']
        exp = self.test1.filter_ids(okseqs)
        self.assertEqual(list(exp.feature_metadata.index.values), okseqs[:-1])
        self.assertIsNot(exp, self.test1)

    def test_filter_ids_samples_inplace_negate(self):
        badsamples = ['S1', 'S3', 'S5', 'S7', 'S9', 'S11', 'S13', 'S15', 'S17', 'S19', 'pita']
        oksamples = list(set(self.test1.sample_metadata.index.values).difference(set(badsamples)))
        exp = self.test1.filter_ids(badsamples, axis=0, negate=True, inplace=True)
        self.assertCountEqual(list(exp.sample_metadata.index.values), oksamples)
        self.assertIs(exp, self.test1)


if __name__ == '__main__':
    main()
