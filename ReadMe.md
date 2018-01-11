secpwgen.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
===========
[wheel](https://gitlab.com/KOLANICH/secpwgen.py/-/jobs/artifacts/master/raw/dist/lime-0.CI-py3-none-any.whl?job=build)
![GitLab Build Status](https://gitlab.com/KOLANICH/secpwgen.py/badges/master/pipeline.svg)
![GitLab Coverage](https://gitlab.com/KOLANICH/secpwgen.py/badges/master/coverage.svg)
[![GitHub Actions](https://github.com/KOLANICH-tools/secpwgen.py/workflows/CI/badge.svg)](https://github.com/KOLANICH-tools/secpwgen.py/actions/)
[![Coveralls Coverage](https://img.shields.io/coveralls/KOLANICH-tools/secpwgen.py.svg)](https://coveralls.io/r/KOLANICH-tools/secpwgen.py)
[![N∅ dependencies](https://shields.io/badge/-N∅_deps!-0F0)


A pure python dropin replacement for [secpwgen](https://linux.die.net/man/1/secpwgen).  Some features are added like QR Code generation.

In order to this work on python<3.6 you need to manually install the [secrets library](https://raw.githubusercontent.com/python/cpython/master/Lib/secrets.py) by downloading it and putting into the dir where default python packages reside.
