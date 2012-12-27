
import logging,os

from gmail import GMailHandler
from message import Message

logger = logging.getLogger("GmailLogger")
logger.setLevel(logging.DEBUG)

gh = gmail.GMailHandler(os.environ['GMAIL_ACCOUNT'].
                        os.envirom['GMAIL_PASSWD'],
                        os.environp'GMAIL_RCPT'],
                        True)

gh.setLevel(logging.DEBUG)
gh.gmail.debug = True

logger.addHandler(gh)

logger.info("Info Message")

