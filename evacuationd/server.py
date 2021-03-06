import logging
import logging.config
import time

from evacuationd import amqp


def main():
    logging.config.fileConfig("/etc/evacuationd/logging.conf")
    logger = logging.getLogger(__name__)

    logger.info('Starting automatic Evacuation daemon...')
    while True:
        try:
            server = amqp.Amqp()
            server.listen()
        except Exception as exc:
            logger.error('Error while connecting to cluster')
            logger.debug(str(exc))
            logging.info('Will wait 5s, and reconnect')
            time.sleep(5)

if __name__ == '__main__':
    main()
