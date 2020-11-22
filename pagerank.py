from page import Page
import mysql.connector
from mysql.connector import errorcode

class PageRank:

    def __init__(self, d = 0.85):
        self.dampingFactor = d  # Dämpfungsfaktor, Standard: 0,85
        self.pageList = dict()  # Liste mit Seiten-Objekten, sodass sie durchlaufen werden können
        self.conn = False # für die DB-Verbindung


    # Programmablauf
    def start(self):

        # Auswählen der Graphenkonstellation
        while True:

            # pageList leeren
            self.pageList = dict()

            print ("Bitte wählen:")
            print ("Beispielgraphen: '1', '2', '3' oder '4'")
            print ("Mediawiki-DB:    'w'")
            print ("beenden:         'exit'")

            command = str(input())

            print ("")

            if command == '1':
                print("Beispielgraph 1:")
                self.exampleOne()
            elif command == '2':
                print("Beispielgraph 2:")
                self.exampleTwo()
            elif command == '3':
                print("Beispielgraph 3:")
                self.exampleThree()
            elif command == '4':
                print("Beispielgraph 4:")
                self.exampleFour()

            elif command == 'w':
                print("Mediawiki-Datenbank:")
                self.mediawikiDatabase()

            elif command == 'exit':
                print ("Tschüss!")
                exit()

            else:
                print ("Falsche Eingabe.")


    # vorgegebene Seitenkonstellationen
    def exampleOne(self):

        PageA = Page("A1", ["B1"])
        PageB = Page("B1", ["A1"])

        self.pageList['A1'] = PageA
        self.pageList['B1'] = PageB

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()

        # Pageranks berechnen
        self.Pagerank()

    def exampleTwo(self):

        PageA = Page("A2", ["C2"])
        PageB = Page("B2", ["A2"])
        PageC = Page("C2", ["B2"])

        self.pageList['A2'] = PageA
        self.pageList['B2'] = PageB
        self.pageList['C2'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()

        # Pageranks berechnen
        self.Pagerank()

    def exampleThree(self):

        PageA = Page("A3", ["B3", "C3"])
        PageB = Page("B3", ["A3", "C3"])
        PageC = Page("C3", [])

        self.pageList['A3'] = PageA
        self.pageList['B3'] = PageB
        self.pageList['C3'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()

        # Pageranks berechnen
        self.Pagerank()

    def exampleFour(self):

        PageA = Page("A4", ["B4"])
        PageB = Page("B4", ["C4"])
        PageC = Page("C4", [])

        self.pageList['A4'] = PageA
        self.pageList['B4'] = PageB
        self.pageList['C4'] = PageC

        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()

        # Pageranks berechnen
        self.Pagerank()


    # Analyse der Mediawiki-Datenbank
    def mediawikiDatabase(self):

        # Verbindungsaufbau zur Datenbank
        self.connectToDB('localhost', 'root', '', 'mediawiki')

        # nicht ausführen, wenn keine Verbindung zur Datenbank möglich ist.
        if not self.conn:
            print("Keine Datenbankverbindung verfügbar!")
            return False # abbrechen

        c = self.conn.cursor()

        # Name & ausgehende Links jeder Seite
        stm = """
            SELECT p.page_title pageName, GROUP_CONCAT(CONVERT(pl.pl_title USING utf8)) linksOut
            FROM page p
            JOIN pagelinks pl
            ON pl.pl_from = p.page_id
            GROUP BY p.page_title
        """
        c.execute(stm)

        # DB Ergebnisse durchlaufen
        for entry in c:
            # group_concat(ausgehende Links) in Liste verwandeln
            links = entry[1].split(',')

            # Seitenobjekt erstellen & zu Liste hinzufügen
            PageX = Page(entry[0], links)
            self.pageList[PageX.name] = PageX


        # eingehende Links ermitteln & in Seiten speichern
        self.findLinksIn()

        # Pageranks berechnen
        self.Pagerank()

    def connectToDB(self, host, user, password, database):

        try:
            self.conn = mysql.connector.connect(
                host=host, user=user, password=password, database=database)
            print("DB Verbindung aufgebaut.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("DB: Invalide Logindaten.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("DB existiert nicht.")
            else:
                print(err)

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
        nextLoop = True


        while nextLoop:

            difference = []


            for key in self.pageList:
                page = self.pageList[key]
                lastRank = page.pagerank
                prT = 0  # hintere Teil der Gleichung ( PR(T1) / C(T1) + ... + PR(Tn) / C(Tn) )

                for link in page.linksIn:
                    otherPage = self.pageList[link]
                    prT += otherPage.pagerank / otherPage.numberLinksOut

                # Berechnung durchführen
                pagerank = 1 - self.dampingFactor + self.dampingFactor * prT
                # Pagerank speichern
                page.setPagerank(pagerank)

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


    # Anzeigen der Seiten und der finalen PRs (sortiert nach dem PR)
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
        print('')


    def createPlaceholder(self, pageName):
        totalChars = 38
        number = totalChars - len(pageName)
        placeholder = number * '_'
        return placeholder


PR = PageRank()
PR.start()