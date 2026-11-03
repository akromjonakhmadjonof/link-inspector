import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Check a website and report where broken links appear."
    )
    parser.add_argument("start_url", help="Website URL to start checking")
    args = parser.parse_args()
    print(args.start_url)


main()
