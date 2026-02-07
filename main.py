"""Thin runtime entrypoint for Ulauncher."""

from ulauncher_gpt.extension import GPTExtension

if __name__ == "__main__":
    GPTExtension().run()
