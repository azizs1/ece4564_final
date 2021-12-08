import yagmail

yag = yagmail.SMTP('ece4564final@gmail.com', 'FinalProject!64')

contents = ['This is the body of the email']

yag.send('nolanp@vt.edu', 'This is the subject', contents)
