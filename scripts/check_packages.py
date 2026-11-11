for pkg in ['PIL', 'selenium', 'playwright', 'pyppeteer', 'matplotlib', 'plotly', 'kaleido']:
    try:
        __import__(pkg)
        print(pkg, ": YES")
    except Exception as e:
        print(pkg, ": NO", type(e).__name__)

