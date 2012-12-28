
import logging,os,unittest

from gmail import GMail,GMailWorker,GMailHandler
from message import Message

class GMailTest(unittest.TestCase):

    def test_gmail(self):
        gmail = GMail(os.environ['GMAIL_ACCOUNT'],
                      os.environ['GMAIL_PASSWD'])
        msg1 = Message('GMail Test Message #1',
                       to=os.environ['GMAIL_RCPT'],
                       text='Hello')
        msg2 = Message('GMail Test Message #2',
                       to=os.environ['GMAIL_RCPT'],
                       text='Hello')
        gmail.send(msg1)
        gmail.send(msg2)
        gmail.close()

    def test_worker(self):
        gmail_worker = GMailWorker(os.environ['GMAIL_ACCOUNT'],
                                   os.environ['GMAIL_PASSWD'])
        msg1 = Message('GMailWorker Test Message #1',
                       to=os.environ['GMAIL_RCPT'],
                       text='Hello')
        msg2 = Message('GMailWorker Test Message #2',
                       to=os.environ['GMAIL_RCPT'],
                       text='Hello')
        gmail_worker.send(msg1)
        gmail_worker.send(msg2)
        gmail_worker.close()

    def test_logging(self):
        logger = logging.getLogger("GMailLogger")
        logger.setLevel(logging.DEBUG)

        gh = GMailHandler(os.environ['GMAIL_ACCOUNT'],
                          os.environ['GMAIL_PASSWD'],
                          os.environ['GMAIL_RCPT'],
                          False)

        gh.setLevel(logging.DEBUG)
        logger.addHandler(gh)

        logger.debug("Debug Message")
        logger.info("Info Message")
        logger.warn("Warn Message")
        logger.error("Error Message")

        try:
            1/0
        except Exception,e:
            logger.exception(e)

        gh.close()

    def test_logging_bg(self):
        logger = logging.getLogger("GMailBackgroundLogger")
        logger.setLevel(logging.DEBUG)

        gh = GMailHandler(os.environ['GMAIL_ACCOUNT'],
                          os.environ['GMAIL_PASSWD'],
                          os.environ['GMAIL_RCPT'],
                          True)

        gh.setLevel(logging.DEBUG)
        logger.addHandler(gh)

        logger.error("Background Error Message")

        gh.close()

if __name__ == '__main__':
    unittest.main()
    
