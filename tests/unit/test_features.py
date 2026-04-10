"""Tests for feature engineering."""
import pytest
from src.features.columns import FEATURE_COLUMNS, TARGET_MAP


class TestFeatureColumns:
    def test_feature_columns_count(self):
        assert len(FEATURE_COLUMNS) == 27

    def test_feature_columns_no_duplicates(self):
        assert len(FEATURE_COLUMNS) == len(set(FEATURE_COLUMNS))


class TestTargetMap:
    def test_target_map_has_all_outcomes(self):
        assert 'H' in TARGET_MAP
        assert 'D' in TARGET_MAP
        assert 'A' in TARGET_MAP

    def test_target_map_convention(self):
        assert TARGET_MAP['A'] == 0
        assert TARGET_MAP['D'] == 1
        assert TARGET_MAP['H'] == 2


class TestFeatureDataFrame:
    def test_sample_features_have_correct_columns(self, sample_features):
        for col in FEATURE_COLUMNS:
            assert col in sample_features.columns
