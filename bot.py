import os
import signal
import sys
import time
import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from slackclient import SlackClient

from kizuna.ClapCommand import ClapCommand
from kizuna.Kizuna import Kizuna
from kizuna.PingCommand import PingCommand
from kizuna.AtGraphCommand import AtGraphCommand
from kizuna.AtGraphDataCollector import AtGraphDataCollector
from kizuna.strings import HAI_DOMO

from raven import Client


def signal_handler(signal, frame):
    print("\nprogram exiting gracefully")
    sys.exit(0)


READ_WEBSOCKET_DELAY = 0.01

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ENVIRONMENT = os.environ.get('KIZUNA_ENV', 'development')
    DEV_INFO = Kizuna.read_dev_info('./.dev-info.json')

    sentry_url = os.environ.get('SENTRY_URL')
    sentry = Client(sentry_url,
                    release=DEV_INFO.get('revision'),
                    environment=ENVIRONMENT) if sentry_url else None

    sc = SlackClient(os.environ.get('SLACK_API_TOKEN'))

    db_engine = create_engine(os.environ.get('DATABASE_URL'))
    Session = sessionmaker(bind=db_engine)

    if sc.rtm_connect():
        auth = sc.api_call('auth.test')
        bot_id = auth['user_id']

        k = Kizuna(bot_id, sc, os.environ.get('MAIN_CHANNEL'))
        print("{} BOT_ID {}".format(HAI_DOMO, bot_id))

        k.handle_startup(DEV_INFO, Session())

        pc = PingCommand()
        k.register_command(pc)

        clap = ClapCommand()
        k.register_command(clap)

        at_graph_command = AtGraphCommand(Session)
        k.register_command(at_graph_command)

        at_graph_data_collector = AtGraphDataCollector(Session, sc)
        k.register_command(at_graph_data_collector)

        while True:
            try:
                read = sc.rtm_read()
                if read:
                    for output in read:
                        if output['type'] == 'message':
                            k.handle_message(output)
            except Exception as e:
                if sentry:
                    sentry.captureException()
                else:
                    print(traceback.format_exc())

            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Can't connect to slack.")
