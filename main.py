"""CSC111 Winter 2026 Project 2: S&P 500 Market Crash Simulator

Main Module
===========

This module is the entry point for running the S&P 500 Market Crash Simulator.
It builds the market network from COVID-19 period data (Jan–Aug 2020) and launches
an interactive Plotly visualization in your web browser.

Instructions:
    1. Ensure sp500_covid_data.json is in the same directory as this file.
    2. Install dependencies: pip install -r requirements.txt
    3. Run this file: python main.py

Copyright and Usage Information
===============================

This file is Copyright (c) 2026 Arnab Karmokar, Brian Chang, Derek Sun, Johnny Li
"""
from visualization import run_visualization

if __name__ == '__main__':
    # Data file and correlation threshold
    DATA_FILE = 'sp500_covid_data.json'
    STRENGTH_THRESHOLD = 0.7

    run_visualization(DATA_FILE, STRENGTH_THRESHOLD)
