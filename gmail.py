
import logging
import multiprocessing
import multiprocessing.queues
import os.path
import smtplib
import time

from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate,make_msgid,getaddresses,parseaddr
from mimetypes import guess_type
from smtplib import SMTPResponseException,SMTPServerDisconnected

version = "0.1"
description = """
        
    gmail_sender
    ------------

    'gmail_sender' provides a simple wrapper around the smtplib/email modules to
    provide an easy programmatic interface for sending email using the GMail SMTP 
    service.

    The module provides the following classes:

    GMail           - Basic interface to GMail SMTP service 
    GMailWorker     - Background worker to send messages asynchronously 
                      (uses multiprocessing module)
    GMailHandler    - GMail handler for logging framework
    Message         - Wrapper around email.Message class simplifying
                      creation of email message objects

    The module also provides a cli interface to send email if run directly
    (python -mgmail)
    
    Changelog:

        *   0.1     2012-10-17  Initial Release

    License:

        *   BSD

    Author:

        *   Paul Chakravarti (paul.chakravarti@gmail.com)
"""

class GMail(object):

    """
        GMail SMTP sender

        Basic usage:

        >>> gmail = GMail('A.User <user@gmail.com>','password')
        >>> msg = Message('Test Message',to='xyz <xyz@xyz.com',text='Hello')
        >>> gmail.send(msg)

    """

    def __init__(self,username,password,debug=False):
        """
            GMail SMTP connection

            username    : GMail username 
                          This can either be a simple address ('user@gmail.com') 
                          or can include a name ('"A User" <user@gmail.com>').
                          
                          The username specified is used as the sender address

            password    : GMail password
            debug       : Debug flag (passed to smtplib)

            The SMTP connection is not opened automatically and requires that
            'connect' is called (the 'send' method will check if the connection
            is open and connect if required). The connection is kept open
            between calls to 'send' to avoid start-up latency and should be
            closed manually if required.

        """
        # Default GMail SMTP address/port
        self.server = 'smtp.gmail.com'
        self.port = 587
        # Parse address componet of username
        self.username = parseaddr(username)[1]
        self.password = password
        self.sender = username
        self.debug = debug
        self.session = None

    def connect(self):
        """
            Connect to GMail SMTP service using smtplib
        """
        self.session = smtplib.SMTP(self.server,self.port)
        self.session.set_debuglevel(self.debug)
        self.session.ehlo()
        self.session.starttls()
        self.session.ehlo()
        self.session.login(self.username,self.password)

    def send(self,message,rcpt=None):
        """
            message         : email.Message instance
            rcpt            : List of recipients (normally parsed from
                              To/Cc/Bcc fields)

            Send message
        """
        # Check if connected and connect if false
        if not self.is_connected():
            self.connect()
        # Extract recipients
        if rcpt is None:
            rcpt = [ addr[1] for addr in getaddresses((message.get_all('To') or []) + 
                                                      (message.get_all('Cc') or []) + 
                                                      (message.get_all('Bcc') or [])) ]
        # Fill in message fileds if not already set
        # NOTE: this modifies the original message and in particular deletes the Bcc field
        if message['From'] is None:
            message['From'] = self.sender
        if message['Reply-To'] is None:
            message['Reply-To'] = self.sender
        if message['Date'] is None:
            message['Date'] = formatdate(time.time(),localtime=True)
        if message['Message-ID'] is None:
            message['Message-ID'] = make_msgid()
        del message['Bcc']

        # Send message
        self.session.sendmail(self.sender,rcpt,message.as_string())

    def is_connected(self):
        """
            Check is session connected - initially by checking session instance and
            then sending NOOP to validate connection

            Sets self.session to None if connection has been closed
        """
        if self.session is None:
            return False
        try:
            rcode,msg = self.session.noop()
            if rcode == 250:
                return True
            else:
                self.session = None
                return False
        except (SMTPServerDisconnected,SMTPResponseException):
            self.session = None
            return False
            
    def close(self):
        """
            Close SMTP connection
        """
        if self.session:
            self.session.quit()
            self.session = None

    def __del__(self):
        """
            Close session on delete
        """
        self.close()

class GMailWorker(object):

    """
        Background GMail SMTP sender

        This class runs a GMail connection object in the background (using 
        the multiprocessing module) which accepts messages through a 
        simple queue. No feedback is provided.

        The object provides a similar api to the Gmail object

        Basic usage:

        >>> gmail_worker = GMailWorker('A.User <user@gmail.com>','password')
        >>> msg = Message('Test Message',to='xyz <xyz@xyz.com',text='Hello')
        >>> gmail_worker.send(msg)

    """
    def __init__(self,username,password,debug=False):
        """
            GMail SMTP connection worker

            username    : GMail username 
                          This can either be a simple address ('user@gmail.com') 
                          or can include a name ('"A User" <user@gmail.com>').
                          
                          The username specified is used as the sender address

            password    : GMail password
            debug       : Debug flag (passed to smtplib)

            Runs '_gmail_worker' helper in background using multiprocessing
            module.

            '_gmail_worker' loops listening for new message objects on the
            shared queue and sends these using the GMail SMTP connection.
        """
        def _gmail_worker(username,password,queue,debug=False):
            gmail = GMail(username,password,debug)
            gmail.connect()
            while True:
                try:
                    msg,rcpt = queue.get()
                    if msg == 'QUIT':
                        break
                    gmail.send(msg,rcpt)
                except SMTPServerDisconnected:
                    gmail.connect()
                    gmail.send(msg,rcpt)
                except SMTPResponseException:
                    pass
                except KeyboardInterrupt:
                    break
            gmail.close()
        self.queue = multiprocessing.queues.SimpleQueue()
        self.worker = multiprocessing.Process(target=_gmail_worker,args=(username,password,self.queue,debug))
        self.worker.start()

    def send(self,message,rcpt=None):
        """
            message         : email.Message instance
            rcpt            : List of recipients (normally parsed from
                              To/Cc/Bcc fields)

            Send message object via background worker
        """
        self.queue.put((message,rcpt))

    def quit(self):
        """
            Close down background worker
        """
        self.queue.put(('QUIT',None))

    def __del__(self):
        self.quit()

class GMmailHandler(logging.Handler):

    def __init__(self,username,password,to,subject,bg=False):
        logging.Handler.__init__(self)
        if bg:
            self.gmail= GMailWorker(username,password)
        else:
            self.gmail= GMail(username,password)
        self.to = to
        self.subject = subject

    def getSubject(self, record):
        return record.levelname + " " + self.subject

    def getText(self,record):
        return str(record)

    def emit(self,record):
        try:
            msg = message(self.getSubject(record),to=self.toaddr,text=self.getText(record))
            msg.body = record.levelname + " " + self.format(record)
            self.gmail.send(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        
class Message(object):
    """
        Wrapper around email.Message class simplifying creation of simple email
        message objects.

        Allows most basic email messages types (including text, html &
        attachments) to be created simply from constructor. More complex
        messages should be created using the email.mime classes directly

        Class wraps the email.Message class and delegates item/attr lookups
        to the wrapped class (allows the object to be treated as a MIMEBase
        instance even though it doesnt inherit from this)

        Basic usage:

        >>> msg = Message('Test Message',to='xyz@xyz.com',text="Hello",html="<b>Hello</b>",attachments=['img.jpg']) 

    """

    def __init__(self,subject,to,cc=None,bcc=None,text=None,html=None,attachments=None):
        """
            Create message object

            subject         : Subject field
            to              : To recipients (as string - eg. "A <a@xyz.com>, B <b@xyz.com>")
            cc              : Cc recipients (same format as to)
            bcc             : Bcc recipients (same format as to)
            text            : Plain text body
            html            : HTML body ('text' will be included as alternative)
            attachments     : List of attachments - if the item is a subclass of MIMEBase
                              this is inserted directly, otherwise it is assumed to be
                              a filename and a MIME attachment craeted guessing the 
                              content-type (for detailed control of the attachment 
                              parameters create these separately)
        """
        if not html and not attachments:
            # Simple plain text email
            self.root = MIMEText(text,'plain',self._charset(text))
        else:
            # Multipart message
            self.root = MIMEMultipart()
            if html:
                # Add html & plain text alernative parts
                alt = MIMEMultipart('alternative')
                alt.attach(MIMEText(text,'plain',self._charset(text)))
                alt.attach(MIMEText(html,'html',self._charset(html)))
                self.root.attach(alt)
            else:
                # Just add plain text part
                txt = MIMEText(text,'plain',self._charset(text))
                self.root.attach(txt)
            # Add attachments
            for a in attachments or []:
                self.root.attach(self._attachment(a))
        # Set headers
        self.root['To'] = to
        if cc: self.root['Cc'] = cc
        if bcc: self.root['Bcc'] = bcc
        self.root['Subject'] = subject

    def _charset(self,s):
        """
            Guess charset - assume ascii for text and force utf-8 for unicode
            (email.mime classes take care of encoding)
        """
        return 'utf-8' if isinstance(s,unicode) else 'us-ascii'

    def _attachment(self,a):
        """
            Create MIME attachment
        """
        if isinstance(a,MIMEBase):
            # Already MIME object - return
            return a
        else:
            # Assume filename - guess mime-type from extension and return MIME object
            main,sub = (guess_type(a) or ('application/octet-stream',''))[0].split('/',1)
            attachment = MIMEBase(main,sub)
            attachment.set_payload(file(a).read())
            attachment.add_header('Content-Disposition','attachment',filename=os.path.basename(a))
            encode_base64(attachment)
            return attachment

    # Delegate to root MIME object (allows object to be treated as MIMEBase)

    def __getitem__(self,key):
        return self.root.__getitem__(key)

    def __setitem__(self,key,value):
        self.root.__setitem__(key,value)

    def __delitem__(self,key):
        return self.root.__delitem__(key)

    def __getattr__(self,attr):
        return getattr(self.root,attr)

def cli():
    import argparse,getpass,mimetypes,sys

    parser = argparse.ArgumentParser(description='Send email message via GMail account')
    parser.add_argument('--username','-u',required=True,
                                help='GMail Username')
    parser.add_argument('--password','-p',default=None,
                                help='GMail Password')
    parser.add_argument('--to','-t',required=True,action='append',default=[],
                                help='To (multiple allowed)')
    parser.add_argument('--cc','-c',action='append',default=[],
                                help='Cc (multiple allowed)')
    parser.add_argument('--subject','-s',required=True,
                                help='Subject')
    parser.add_argument('--body','-b',
                                help='Message Body (text)')
    parser.add_argument('--html','-l',default=None,
                                help='Message Body (html)')
    parser.add_argument('--attachment','-a',action='append',default=[],
                                help='Attachment (multiple allowed)')
    parser.add_argument('--debug','-d',action='store_true',default=False,
                                help='Debug')

    results = parser.parse_args()

    if results.password is None:
        results.password = getpass.getpass("Password:")

    if results.body is None and results.html is None:
        results.body = sys.stdin.read()

    gmail = GMail(username=results.username,
                  password=results.password,
                  debug=results.debug)
    msg = Message(subject=results.subject,
                  to=",".join(results.to),
                  cc=",".join(results.cc),
                  text=results.body,
                  html=results.html,
                  attachments=results.attachment)
    gmail.send(msg)
    gmail.close()

if __name__ == '__main__':
    cli()
