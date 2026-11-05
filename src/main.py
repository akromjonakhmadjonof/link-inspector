import argparse

from .urls import validate_start_url


def main():
    parser = argparse.ArgumentParser(
        description="Check a website and report where broken links appear."
    )
    parser.add_argument("start_url", help="Website URL to start checking")
    args = parser.parse_args()
    try:
        start_url = validate_start_url(args.start_url)
    except ValueError as error:
        parser.error(str(error))
    print(start_url)


main()
