from page import Page
import mysql.connector
from mysql.connector import errorcode

class PageRank:

    def __init__(self, d = 0.85):
        self.dampingFactor = d
        self.pageList = dict() # Liste mit Seiten-Objekten
        # Datenbankverbindung
        self.conn = False
        try:
            self.conn = mysql.connector.connect(
                host="localhost", user="root", password="", database="mediawiki")
            print("DB Verbindung aufgebaut.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)


    # Programmablauf
    def start(self):
        while True:
            print ("Bitte wählen:")
            print ("Beispielgraphen: '1', '2', '3' oder '4'")
            print ("WikiMedia DB:    'w'")
            print ("beenden:         'e'")

            command = str(input())

            if command == '1':
                self.exampleOne()
            elif command == '2':
                self.exampleTwo()
            elif command == '3':
                self.exampleThree()
            elif command == '4':
                self.exampleFour()

            elif command == 'w':
                self.wikiDatabase()

            elif command == 'e':
                exit()

            else:
                print ("Falsche Eingabe.")


    # vorgegebene Seitenkonstellationen
    def exampleOne(self):

        PageA = Page("A1", ["B1"])
        PageB = Page("B1", ["A1"])

        self.pageList = dict()
        self.pageList['A1'] = PageA
        self.pageList['B1'] = PageB

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()
        print("")
        print("Ergebnisse Aufgabe 1:")
        # Pageranks berechnen
        self.Pagerank()

    def exampleTwo(self):

        PageA = Page("A2", ["C2"])
        PageB = Page("B2", ["A2"])
        PageC = Page("C2", ["B2"])

        self.pageList = dict()
        self.pageList['A2'] = PageA
        self.pageList['B2'] = PageB
        self.pageList['C2'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()
        print("")
        print("Ergebnisse Aufgabe 2:")
        # Pageranks berechnen
        self.Pagerank()

    def exampleThree(self):

        PageA = Page("A3", ["B3", "C3"])
        PageB = Page("B3", ["A3", "C3"])
        PageC = Page("C3", [])

        self.pageList = dict()
        self.pageList['A3'] = PageA
        self.pageList['B3'] = PageB
        self.pageList['C3'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()
        print("")
        print("Ergebnisse Aufgabe 3:")
        # Pageranks berechnen
        self.Pagerank()

    def exampleFour(self):

        PageA = Page("A4", ["B4"])
        PageB = Page("B4", ["C4"])
        PageC = Page("C4", [])

        self.pageList = dict()
        self.pageList['A4'] = PageA
        self.pageList['B4'] = PageB
        self.pageList['C4'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()
        print("")
        print("Ergebnisse Aufgabe 4:")
        # Pageranks berechnen
        self.Pagerank()


    # Analyse der Wiki-Datenbank
    def wikiDatabase(self):
        if not self.conn:
            print("Keine Datenbankverbindung verfügbar")
            return False

        c = self.conn.cursor()

        # Namen aller Seiten + Namen der Seiten, auf die sie zeigen
        stm = """
            SELECT p.page_title pageName, GROUP_CONCAT(CONVERT(pl.pl_title USING utf8)) linksOut
            FROM page p
            JOIN pagelinks pl
            ON pl.pl_from = p.page_id
            GROUP BY p.page_title
        """
        c.execute(stm)

        # pageList leeren
        self.pageList = dict()

        # DB Ergebnisse durchlaufen
        for entry in c:

            links = entry[1].split(',')

            PageX = Page(entry[0], links)
            self.pageList[PageX.name] = PageX


        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()
        print("")
        print("Ergebnisse der Wiki-DB:")
        # Pageranks berechnen
        self.Pagerank()


    # eingehende Links aller Seiten ermitteln
    def findLinksIn(self):

        for key in self.pageList:
            page = self.pageList[key]
            name = str(page.name)
            linksIn = []

            for otherKey in self.pageList:
                otherPage = self.pageList[otherKey]

                for index, link in enumerate(otherPage.linksOut):
                    if link: # leere linksOut verursacht sonst Fehler
                        link = link # list item
                        if link == name:
                            linksIn.append(otherPage.name)

            # in Seite speichern
            page.setLinksIn(linksIn)  #Page.setLinksIn(page, linksIn)


    def Pagerank(self):
        counter = 1 # Zählen der Durchläufe
        nextLoop = True # zum abbrechen der Schleife


        while nextLoop:

            difference = []

            # Durchlauf Nr.:
            #print ('----------------------------------')
            #print(f"{counter}. Durchlauf:")

            for key in self.pageList:
                page = self.pageList[key]
                lastRank = page.pagerank
                prT = 0  # hintere Teil der Gleichung ( PR(T) / C(T) )

                for link in page.linksIn:
                    otherPage = self.pageList[link]
                    prT += otherPage.pagerank / otherPage.numberLinksOut

                # Berechnung durchführen
                pagerank = 1 - self.dampingFactor + self.dampingFactor * prT
                # Pagerank speichern
                page.setPagerank(pagerank)

                #print(f"PR({page.name}) = {round(page.pagerank, 4)}")

                difference.append(self.calculateDifference(lastRank, pagerank))


            # Schleife wird beendet, wenn die Veränderungen der PRs aller Seiten im Vergleich zum vorigen PR < 0.1% sind
            x = False
            for diff in difference:
                if diff >= 0.1:
                    x = True
            if not x:
                nextLoop = False
                print (f"{counter} Durchläufe benötigt")
                sumPageranks = self.getPRSum()
                print (f"Summe aller Pageranks = {sumPageranks}")

            # Anzahl Durchläufe
            counter = counter + 1

        self.showResults()

    # Unterschied in % zum letzten PR errechnen
    def calculateDifference(self, lastRank, thisRank):
        difference = abs(lastRank - thisRank) / lastRank *100
        #print (f"Unterschied zu letztem PR = {round(difference, 1)} %")
        #print ('')
        return difference

    # Gesamtsumme aller PRs berechnen
    def getPRSum(self):
        sumPR = 0

        for key in self.pageList:
            page = self.pageList[key]
            sumPR += page.pagerank
        return sumPR



    # Anzeigen der Seiten und deren finalen PRs (sortiert nach dem PR)
    def showResults(self):
        print ('')
        print ("Pageranks:")
        pageranks = []

        for key in self.pageList:
            page = self.pageList[key]

            pageranks.append([page.pagerank, page.name]) #pagerank zum Sortieren zuerst
            pageranks.sort(reverse=True)

        i = 0
        for page in pageranks:
            p = self.createPlaceholder(page[1])

            if i < 10:
                j = "0" + str(i)
            else:
                j = i
            print(f"{j}. {page[1]}{p} {page[0]}")
            i += 1
        print("")


    def createPlaceholder(self, pageName):
        totalChars = 38
        number = totalChars - len(pageName)
        placeholder = number * '_'
        return placeholder


PR = PageRank()
PR.start()