#!/usr/bin/env python3
# # flake8: noqa
"""
Main Freqtrade bot script.
Read the documentation to know what cli arguments you need.
"""
import logging
import sys
from typing import Any, List, Optional

from freqtrade.util.gc_setup import gc_set_threshold


# check min. python version
if sys.version_info < (3, 9):  # pragma: no cover
    sys.exit("Freqtrade requires Python version >= 3.9")

from freqtrade import __version__
from freqtrade.commands import Arguments
from freqtrade.exceptions import FreqtradeException, OperationalException
from freqtrade.loggers import setup_logging_pre


logger = logging.getLogger('freqtrade')


def main(sysargv: Optional[List[str]] = None) -> None:
    """
    This function will initiate the bot and start the trading loop.
    :return: None
    """
    debug_input = input('Debug mode? (y/n): ')
    if debug_input == 'y':
        try:
            import os
            working_directory = '/allah/freqtrade'
            os.chdir(working_directory)
            print('Welcome to Freqtrade! This is the Machine learning branch.')
            config_trade = ['--version']

            # config_backtest = ['backtesting', '-c', 'config.json', '--timerange', '20231004-', '--timeframe', '1m', '--strategy', 'MacdStrategyLong', '--eps', '--starting-balance', '1000000000', '--cache', 'none']
            # config_backtest = ['backtesting', '-c', 'fake_1m_config.json', '--timerange', '20230219-20230220', '--timeframe', '1m', '--strategy', 'MacdStrategyLong', '--eps', '--starting-balance', '1000000000', '--cache', 'none']
            # config_backtest = ['backtesting', '-c', 'fake_1m_config.json', '--timerange', '19900101-', '--timeframe', '1m', '--strategy', 'fake_1m_strat_long', '--starting-balance', '1000', '--cache', 'none', '--export', 'signals']
            config_backtest = ['backtesting', '-c', 'fake_1m_config.json', '--timerange', '19900101-', '--timeframe', '1m', '--strategy', 'fake_1m_strat_long', '--starting-balance', '1000', '--cache', 'none']
            # config_backtest = ['backtesting', '-c', 'config.json', '--timerange', '20230219-20230220', '--timeframe', '1m', '--strategy', 'MacdStrategyLong', '--eps', '--starting-balance', '1000000000', '--cache', 'none']

            sysargv = config_backtest
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
        if 'func' in args:
            logger.info(f'freqtrade {__version__}')
            gc_set_threshold()
            return_code = args['func'](args)
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
        logger.info('SIGINT received, aborting ...')
        return_code = 0
    except FreqtradeException as e:
        logger.error(str(e))
        return_code = 2
    except Exception:
        logger.exception('Fatal exception!')
    finally:
        sys.exit(return_code)


if __name__ == '__main__':  # pragma: no cover
    main()
