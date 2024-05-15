#!/usr/bin/env python3
# # flake8: noqa
"""
Main Freqtrade bot script.
Read the documentation to know what cli arguments you need.
"""

import logging
import sys
from typing import Any, List, Optional


# check min. python version
if sys.version_info < (3, 9):  # pragma: no cover
    sys.exit("Freqtrade requires Python version >= 3.9")

from freqtrade import __version__
from freqtrade.commands import Arguments
from freqtrade.constants import DOCS_LINK
from freqtrade.exceptions import ConfigurationError, FreqtradeException, OperationalException
from freqtrade.loggers import setup_logging_pre
from freqtrade.util.gc_setup import gc_set_threshold


logger = logging.getLogger("freqtrade")


def main(sysargv: Optional[List[str]] = None) -> None:
    """
    This function will initiate the bot and start the trading loop.
    :return: None
    """
    # debug_input = input('Debug mode? (y/n): ')
    debug_input = 0
    if debug_input == 1:
        try:
            import os
            working_directory = '/allah/freqtrade'
            os.chdir(working_directory)
            print('Welcome to Freqtrade! This is the Machine learning branch.')

            # config = [
            #     'backtesting',
            #     '-c', 'config.json',
            #     '--timerange', '20231111-',
            #     '--timeframe', '1m',
            #     '--strategy', 'LuxAlgoTEMA20Strategy',
            #     '--starting-balance', '1000',
            #     '--cache', 'none',
            #     '--eps'
            # ]
            config = [
                    "hyperopt",
                    "--hyperopt-loss", "SharpeHyperOptLossDaily",
                    "--spaces", "stoploss",
                    "--strategy", "LuxAlgoTEMA20Strategy_follow",
                    "-c", "config.json",
                    "-e", "100",
                    "--timerange", "20231201-",
                    "--timeframe", "1m"
                ]


            sysargv = config

        except Exception as e:
            print(e)
    else:
        pass


    return_code: Any = 1

    try:
        setup_logging_pre()
        arguments = Arguments(sysargv)
        args = arguments.get_parsed_arg()

        # Call subcommand.
        if "func" in args:
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
