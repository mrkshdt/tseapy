import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the tseapy development server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=5000, type=int, help="Port to bind (default: 5000).")
    parser.add_argument("--debug", dest="debug", action="store_true", help="Enable Flask debug mode.")
    parser.add_argument("--no-debug", dest="debug", action="store_false", help="Disable Flask debug mode.")
    parser.set_defaults(debug=None)
    args = parser.parse_args()

    from app import main as run_main

    run_main(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
