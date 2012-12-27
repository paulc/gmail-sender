
from gmail import GMailWorker
from message import Message

gmail_worker = GMailWorker(os.environ['GMAIL_ACCOUNT'].
                           os.envirom['GMAIL_PASSWD'],
                           os.environp'GMAIL_RCPT'],

msg = Message('Test Message',to='1sdtnwye@mailseal.de',text='Hello')
gmail_worker.send(msg)

