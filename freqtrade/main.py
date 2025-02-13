#!/usr/bin/env python3
"""
Main Freqtrade bot script.
Read the documentation to know what cli arguments you need.
"""

import logging
import sys
from typing import Any


# check min. python version
if sys.version_info < (3, 10):  # pragma: no cover  # noqa: UP036
    sys.exit("Freqtrade requires Python version >= 3.10")

from freqtrade import __version__
from freqtrade.commands import Arguments
from freqtrade.constants import DOCS_LINK
from freqtrade.exceptions import ConfigurationError, FreqtradeException, OperationalException
from freqtrade.loggers import setup_logging_pre
from freqtrade.system import asyncio_setup, gc_set_threshold, print_version_info


logger = logging.getLogger("freqtrade")

import re


def update_identifier_directly(config_path: str):
    try:
        # Read the file as text
        with open(config_path, "r") as file:
            content = file.read()

        # Use regex to find and update the identifier value
        match = re.search(r'"identifier":\s*"unique-id-(\d+)"', content)
        if match:
            current_id = int(match.group(1))  # Extract the current ID
            new_id = current_id + 1  # Increment the ID
            new_identifier = f'"identifier": "unique-id-{new_id}"'

            # Replace the old identifier with the new one
            updated_content = re.sub(r'"identifier":\s*"unique-id-\d+"', new_identifier, content)

            # Write the updated content back to the file
            with open(config_path, "w") as file:
                file.write(updated_content)

            print(f"Updated identifier to unique-id-{new_id}")
        else:
            print("Identifier not found in the configuration file.")
    except Exception as e:
        print(f"Error updating identifier: {e}")


def main(sysargv: list[str] | None = None) -> None:
    """
    This function will initiate the bot and start the trading loop.
    :return: None
    """

    # Initialize debug mode (set to 1 to enable, 0 to disable)

    # update_identifier_directly("/allah/stuff/freq/userdir/config_freqai.json")
    debug_input = 0
    if debug_input == 1:
        try:
            import os

            working_directory = "/allah/freqtrade"
            os.chdir(working_directory)

            config_1 = [
                "backtesting-analysis",
                "-c",
                "/allah/stuff/freq/userdir/user_data/mutiple_coins_BT_v1.json",
                "--userdir",
                "/allah/stuff/freq/userdir/user_data",
                "--indicator-list",
                "trend",
                "close_date",
                "profit_ratio",
                "--timerange",
                "20241222-20241223",
            ]

            config_1 = [
                "backtesting",
                "--strategy",
                "MultiTimeframeTEMAAgreement",
                "--userdir",
                "/allah/stuff/freq/userdir/user_data",
                "--config",
                "/allah/stuff/freq/userdir/user_data/mutiple_coins_BT_v1_THEUSDT.json",
                "--timerange",
                "20241222-20241223",
                "--datadir",
                "/allah/freqtrade/user_data/data/binance",
                "--cache",
                "none",
                "--starting-balance",
                "10000",
                "--eps",
                "--export",
                "signals",
            ]

            sysargv = config_1

        except Exception as e:
            print(f"Error in debug mode setup: {e}")

    return_code: Any = 1
    try:
        setup_logging_pre()
        asyncio_setup()
        arguments = Arguments(sysargv)
        args = arguments.get_parsed_arg()

        # Call subcommand.
        if args.get("version") or args.get("version_main"):
            print_version_info()
            return_code = 0
        elif "func" in args:
            logger.info(f"freqtrade {__version__}")
            gc_set_threshold()
            return_code = args["func"](args)
        else:
            # No subcommand was issued.
            raise OperationalException(
                "Usage of Freqtrade requires a subcommand to be specified.\n"
                "To have the bot executing trades in live/dry-run modes, "
                "depending on the value of the `dry_run` setting in the config, run Freqtrade "
                "as `freqtrade trade [options...]`.\n"
                "To see the full list of options available, please use "
                "`freqtrade --help` or `freqtrade <command> --help`."
            )

    except SystemExit as e:  # pragma: no cover
        return_code = e
    except KeyboardInterrupt:
        logger.info("SIGINT received, aborting ...")
        return_code = 0
    except ConfigurationError as e:
        logger.error(
            f"Configuration error: {e}\n"
            f"Please make sure to review the documentation at {DOCS_LINK}."
        )
    except FreqtradeException as e:
        logger.error(str(e))
        return_code = 2
    except Exception:
        logger.exception("Fatal exception!")
    finally:
        sys.exit(return_code)


if __name__ == "__main__":  # pragma: no cover
    main()
