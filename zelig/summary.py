import json
import os
import time

from zelig.constants import FILES_DIRECTORY, METADATA_FILE, SUMMARY_ARGUMENT
from zelig.log import logger


def get_summary_text(mode, report_dir, total_played, reports_number, started, finished, **kwargs):
    return (
    f"""Summary of '{report_dir}' recorded in '{mode}' mode:
    Total requests played: {total_played}
        Successful: {total_played - reports_number}
        Reports generated: {reports_number}
    Started at: {time.ctime(started)}
    Finished at: {time.ctime(finished)}
    Elapsed time: {round(finished-started, 4)} sec"""
    )


def print_summary(args):
    if len(args) == 2 and args[0] == SUMMARY_ARGUMENT:
        report_dir = args[1]
        metadata_path = os.path.join(FILES_DIRECTORY, report_dir, METADATA_FILE)
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                try:
                    data = json.loads(f.read())
                    print(get_summary_text(report_dir=report_dir, **data))
                    return
                except json.JSONDecodeError as e:
                    logger.error(f'Could not read metadata file. {e!s}')
        else:
            logger.error(f'Could not find metadata file. Check if you\'ve mounted \'{FILES_DIRECTORY}\' folder'
                         f' and \'{METADATA_FILE}\' file exists')
    else:
        logger.error(f'Could not parse arguments "{args}". Please use "zelig summary <folder_name>" command')
    exit(1)
