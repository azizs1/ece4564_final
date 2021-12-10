import yagmail

yag = yagmail.SMTP('ece4564final@gmail.com', 'FinalProject!64')

contents = ["[['Apple (AAPL) Stock Sinks As Market Gains: What You Should Know', 'http://www.zacks.com/stock/news/1834785/apple-aapl-stock-sinks-as-market-gains-what-you-should-know?cid=CS-ENTREPRENEUR-FT-tale_of_the_tape|yseop_template_6-1834785'], ['AAPL Stock Sets New All-Time High Following Latest Apple Car Rumors', 'https://www.macrumors.com/2021/11/18/aapl-all-time-high-car-rumors/'], [': Insider buying says a Santa Claus rally is on the way — here are 10 stocks they favor', 'https://www.marketwatch.com/story/insider-buying-says-a-santa-claus-rally-is-on-the-way-here-are-10-stocks-they-favor-11638541634'], ['The FAANG Market Is Fading', 'https://www.morningstar.com/articles/1070180/the-faang-market-is-fading']]"]

yag.send('nolanp@vt.edu', 'This is the subject', contents)

