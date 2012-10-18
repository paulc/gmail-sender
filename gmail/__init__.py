
from gmail import GMail,GMailWorker,GMailHandler
from message import Message

version = "0.2"
description = """
        
    gmail
    -----

    The 'gmail' module provides a simple wrapper around the smtplib/email
    modules to provide an easy programmatic interface for sending email using
    the GMail SMTP service.

    The module provides the following classes:

    GMail           - Basic interface to GMail SMTP service 
    GMailWorker     - Background worker to send messages asynchronously 
                      (uses multiprocessing module)
    GMailHandler    - GMail handler for logging framework
    Message         - Wrapper around email.Message class simplifying
                      creation of email message objects

    The module also provides a cli interface to send email if run directly
    (python -mgmail.cli)
    
    Changelog:

        *   0.1     2012-10-17  Initial Release
        *   0.2     2012-10-18  Restructure module

    License:

        *   BSD

    Author:

        *   Paul Chakravarti (paul.chakravarti@gmail.com)
"""

