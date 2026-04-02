from visualization import run_visualization

if __name__ == '__main__':
    DATA_FILE = 'sp500_covid_data.json'
    STRENGTH_THRESHOLD = 0.7

    run_visualization(DATA_FILE, STRENGTH_THRESHOLD)
