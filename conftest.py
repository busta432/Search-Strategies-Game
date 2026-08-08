# Ensures search.py (at the project root) is importable from tests/ no
# matter what working directory or rootdir pytest is invoked from - VS
# Code's Test Explorer in particular doesn't always honour pytest.ini's
# `pythonpath` setting.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
