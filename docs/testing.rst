Testing and coverage
====================

The test suite lives in ``tests/`` and uses `pytest <https://docs.pytest.org/>`_.

Run locally
-----------

.. code-block:: bash

   pip install -e ".[test]"
   pytest

With coverage report:

.. code-block:: bash

   pytest --cov=loanpy --cov-report=term-missing

HTML report:

.. code-block:: bash

   pytest --cov=loanpy --cov-report=html
   # open htmlcov/index.html

What is covered
---------------

Tests exercise the public API end-to-end:

* **edit** — LCS-based distance, DP matrix, shortest path, edit operations
* **cluster** — CV clustering, glide clustering, liquid clustering
* **align** — ``Uralign`` sequential alignment; ``Altign`` gap collapsing and cluster-aware scoring
* **correspondences** — alternating-row validation, correspondence mining, TOML export/load round-trip
* **phonotactics** — template expansion and nearest-template selection
* **adapt** — substitution learning, mapping, and repair
* **package** — version string and ``__all__`` exports

Continuous integration
----------------------

GitHub Actions runs two install paths: an editable install from the checkout
(``pip install -e ".[test]"``), and a second job that installs from the latest
``main`` on GitHub (``pip install git+https://github.com/loanwordbank/loanpy.git@main``)
and runs the same tests. Coverage is measured on Python 3.12 and uploaded to
`Codecov <https://codecov.io/gh/loanwordbank/loanpy>`__ (badge in the README).
See ``.github/workflows/tests.yml``.

Coverage expectations
---------------------

On the current 4.0 test suite, line coverage on ``loanpy/`` is about **99%**
(103 tests; run ``pytest --cov=loanpy`` locally for an exact figure). Coverage is
informational: linguistic pipelines should still be validated on real CLDF
datasets in downstream projects.
