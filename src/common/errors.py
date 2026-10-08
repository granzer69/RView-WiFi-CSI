"""Errors raised by the data pipeline."""


class DatasetError(Exception):
    """A dataset file or record is unusable."""


class LabelMapError(DatasetError):
    """A filename activity code and a class folder disagree."""


class SplitError(Exception):
    """A split request cannot be satisfied without leaking or dropping groups."""


class LicenseError(Exception):
    """A dataset is not cleared for experiments or publication."""
