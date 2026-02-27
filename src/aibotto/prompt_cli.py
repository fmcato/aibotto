"""
CLI interface for AIBOTTO - allows sending prompts from command line.
"""

import argparse
import asyncio
import logging
import sys

from aibotto.ai.tool_calling import AgenticOrchestrator
from aibotto.config.settings import Config
from aibotto.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="aibotto-cli",
        description="Send a prompt to AIBOTTO and get a response",
    )
    parser.add_argument(
        "prompt",
        nargs="+",
        help="The prompt to send to the AI assistant",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


async def run_prompt(prompt: str) -> str:
    """Run a single prompt through the tool calling manager."""
    manager = AgenticOrchestrator()
    return await manager.process_prompt_stateless(prompt)


def main() -> None:
    """Main entry point for CLI interface."""
    args = parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "WARNING"
    setup_logging(level=log_level)

    # Validate configuration
    if not Config.validate_config():
        print("Error: Configuration validation failed", file=sys.stderr)
        sys.exit(1)

    # Join prompt parts
    prompt = " ".join(args.prompt)

    if args.verbose:
        print(f"Sending prompt: {prompt}", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    # Run the prompt
    try:
        response = asyncio.run(run_prompt(prompt))
        print(response)
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
