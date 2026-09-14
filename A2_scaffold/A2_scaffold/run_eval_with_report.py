#!/usr/bin/env python3
"""
Wrapper script for run_eval.py that sets the correct data path
and generates both JSON and TXT reports.
"""
import os
import sys

# Set the data path before importing other modules
os.environ['A2_DATA'] = r'd:\Github\PE6201_A2\A2_reference_data\A2_reference_data'

# Now import and run
import run_eval

if __name__ == "__main__":
    sys.exit(run_eval.main(sys.argv))
