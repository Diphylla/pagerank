class Page:

    def __init__(self, name, linksOut):
        self.name = name
        self.linksOut = linksOut
        self.numberLinksOut = len(self.linksOut)
        self.linksIn = [] # Namen der Seiten, die auf diese zeigen
        self.pagerank = 1


    def setLinksIn(self, newLinkIn):
        self.linksIn = newLinkIn

    def setPagerank(self, PR):
        self.pagerank = PR

