from .app import SpiderApp

def main() -> None:
    """Run the Spider solitaire TUI application."""
    app = SpiderApp()
    app.run()

if __name__ == "__main__":
    main()