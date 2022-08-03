# <img alt="cotat" src="branding/cotat_color.png" height="90">

[![CircleCI](https://circleci.com/gh/cornell-covid-modeling/cotat/tree/master.svg?style=shield&circle-token=97897740e926742355ec6f2809bb29815c07a1fb)](https://circleci.com/gh/cornell-covid-modeling/cotat/tree/master)
[![codecov](https://codecov.io/gh/cornell-covid-modeling/cotat/branch/master/graph/badge.svg?token=59BOEOE7TB)](https://codecov.io/gh/cornell-covid-modeling/cotat)

cotat is a visualization tool for the analysis of contact tracing data. Given
a dataframe of people (along with their attributes) and a dataframe of
known contacts among the individuals, cotat exports an interactive HTML
visualization of the network. Furthermore, certain columns of the people
dataframe can be labeled as "membership columns" which allows one to visualize
which people belong to the same groups (e.g. building, club, etc..) even if
a contact between those individuals has not been reported.

## Examples

![example.png](example.png)

## Installation

This Python package is not yet posted on [PyPI](https://pypi.org). Hence,
the best way to get started is by cloning the repo and pip installing.

```
git clone git@github.com:cornell-covid-modeling/cotat.git
cd cotat
pip install -e .
```

## License

Licensed under the [MIT License](https://choosealicense.com/licenses/mit/)
