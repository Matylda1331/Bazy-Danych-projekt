from pylatex import Document, Section, Subsection, Tabular, NoEscape, Command, Center
import mysql.connector
import os
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import pandas as pd

con = mysql.connector.connect(
    host = "giniewicz.it",
    user = "team19",
    password = "te@mzaiq",
    database = "team19"
)

cursor = con.cursor()

#PYTANIE 1

#nazwy wycieczek
cursor.execute("SELECT id_rodzaj, Nazwa FROM Rodzaje_wycieczek")
wynik = cursor.fetchall()

Nazwy_wycieczek = []
for row in wynik:
    id_rodzaj = int(row[0])
    nazwa = row[1]
    Nazwy_wycieczek.append((id_rodzaj, nazwa))
#zliczanie ilości osób ktore pojechały na daną wycieczke
cursor.execute('''SELECT Rodzaje_wycieczek.id_rodzaj,
COUNT(DISTINCT Rezerwacje.id_rezerwacje)
FROM Rezerwacje JOIN Realizowane_wycieczki
ON Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
JOIN Rodzaje_wycieczek
ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
WHERE Rezerwacje.id_transakcje IN 
(SELECT id_transakcje FROM Transakcje_finansowe
WHERE Zrealizowano = 1)
GROUP BY Rodzaje_wycieczek.id_rodzaj
ORDER BY Rodzaje_wycieczek.id_rodzaj;''')

wynik = cursor.fetchall()

Ilosc_osob = []
for row in wynik:
    id_rodzaj = int(row[0])
    ilosc = int(row[1])
    Ilosc_osob.append((id_rodzaj, ilosc))

#zliczanie kosztów zrealizowanych wycieczek z podziałem na rodzaj
cursor.execute('''SELECT Rodzaje_wycieczek.id_rodzaj AS id,
SUM(Koszty_organizacji.Nocleg_za_noc * 
(DATEDIFF(Realizowane_wycieczki.Data_zakonczenia, Realizowane_wycieczki.Data_rozpoczecia) - 2)
+ Koszty_organizacji.Przewodnik
+ Koszty_organizacji.Loty
+ Koszty_organizacji.Atrakcje
+ Koszty_organizacji.Ubezpieczenie
+ Koszty_organizacji.Transport
)*(SELECT COUNT(DISTINCT Rezerwacje.id_rezerwacje)
FROM Rezerwacje JOIN Realizowane_wycieczki
ON Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
JOIN Rodzaje_wycieczek
ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
WHERE Rezerwacje.id_transakcje IN 
(SELECT id_transakcje FROM Transakcje_finansowe
WHERE Zrealizowano = 1)
AND Rezerwacje.id_wycieczki = id)
FROM Koszty_organizacji JOIN Realizowane_wycieczki
ON Koszty_organizacji.id_koszty = Realizowane_wycieczki.id_koszty
JOIN Rodzaje_wycieczek 
ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
WHERE Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
AND Koszty_organizacji.id_koszty = Realizowane_wycieczki.id_koszty
GROUP BY Rodzaje_wycieczek.id_rodzaj
ORDER BY Rodzaje_wycieczek.id_rodzaj;''')

#wyniki
wyniki = cursor.fetchall()

Suma_koszty = [] #w tej tablicy po kolei koszty kazdego rodzaju wycieczki
for row in wyniki:
    id_rodzaj = row[0]
    koszt_suma = row[1]
    Suma_koszty.append((id_rodzaj, float(koszt_suma)))

#Zyski_rodzaj całkowite na każdą wycieczkę 
cursor.execute('''
SELECT Rodzaje_wycieczek.id_rodzaj AS id,
SUM(Realizowane_wycieczki.Cena_za_osobe*
(SELECT COUNT(DISTINCT Rezerwacje.id_rezerwacje)
FROM Rezerwacje JOIN Realizowane_wycieczki
ON Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
JOIN Rodzaje_wycieczek
ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
WHERE Rezerwacje.id_transakcje IN 
(SELECT id_transakcje FROM Transakcje_finansowe
WHERE Zrealizowano = 1)
AND Rezerwacje.id_wycieczki = id))
FROM Realizowane_wycieczki JOIN Rodzaje_wycieczek
ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
GROUP BY Rodzaje_wycieczek.id_rodzaj
ORDER BY Rodzaje_wycieczek.id_rodzaj;''')

wyniki = cursor.fetchall()

Suma_przychod = [] #w tej tablicy po kolei przychód z kazdego rodzaju wycieczki
for row in wyniki:
    id_rodzaj = row[0]
    przychod_suma = row[1]
    Suma_przychod.append((id_rodzaj, float(przychod_suma)))

Zyski_rodzaj = []
for i in range(len(Suma_koszty)):
    indeks, koszt = Suma_koszty[i]
    _, przychod = Suma_przychod[i]
    zysk = przychod - koszt
    Zyski_rodzaj.append((indeks, zysk))

min_zysk_rodzaj = min(Zyski_rodzaj, key=lambda x: x[1])  #najmniejszy zysk
max_zysk_rodzaj = max(Zyski_rodzaj, key=lambda x: x[1])  #najwiekszy zysk
suma_zysk_rodzaj = sum(x[1] for x in Zyski_rodzaj)

#PYTANIE 2
cursor.execute("""
SELECT 
    DATE_FORMAT(Data_rezerwacji, '%Y-%m') AS Miesiac,
    COUNT(DISTINCT id_klienci) AS Liczba_Klientow
FROM Rezerwacje
GROUP BY Miesiac
ORDER BY Miesiac;
""")

wynik2 = cursor.fetchall()
######################################
months_liczba_klientow = [row[0] for row in wynik2]
liczba_klientow = [row[1] for row in wynik2]
miesiac_rez = []
for row in wynik2:
    mies = row[0]
    ile  = int(row[1])
    miesiac_rez.append((mies,ile))

query = """
SELECT 
    DATE_FORMAT(rw.data_rozpoczecia, '%Y-%m') AS Miesiac,
    COUNT(DISTINCT r.id_klienci) AS Liczba_Osob
FROM Rezerwacje r
JOIN Realizowane_wycieczki rw ON r.id_wycieczki = rw.id_wycieczki
GROUP BY Miesiac
ORDER BY Miesiac;
"""

data_miesiace = pd.read_sql(query, con)

cursor.execute(query)
result = cursor.fetchall()
wyjazdy_na_miesiac = []
for row in result:
    mies, ile = row
    wyjazdy_na_miesiac.append((mies, ile))

####################################
cursor.execute("""
SELECT YEAR(rw.data_rozpoczecia) AS rok, MONTH(rw.data_rozpoczecia) AS miesiac, 
       COUNT(DISTINCT r.id_klienci) AS liczba_osob
FROM Rezerwacje r
JOIN Realizowane_wycieczki rw ON r.id_wycieczki = rw.id_wycieczki
GROUP BY rok, miesiac
ORDER BY rok, miesiac;
""")
results = cursor.fetchall()

months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", 
          "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]

data_ilosc_mies = {month: 0 for month in months}

for row in results:
    year, month_number, count = row
    data_ilosc_mies[months[month_number - 1]] += count
iloscmies = []
suma_ilosc_rok = {}
for row in results:
    rok, mies, ile = row
    iloscmies.append((rok,mies,ile))
    if rok in suma_ilosc_rok:
        suma_ilosc_rok[rok] += ile
    elif rok != 2025:
        suma_ilosc_rok[rok] = ile

suma_ilosc_rok = list(suma_ilosc_rok.items())
#######################################################
cursor.execute("""
SELECT YEAR(rw.data_rozpoczecia) AS rok, MONTH(rw.data_rozpoczecia) AS miesiac, 
       COUNT(DISTINCT r.id_klienci) AS liczba_osob
FROM Rezerwacje r
JOIN Realizowane_wycieczki rw ON r.id_wycieczki = rw.id_wycieczki
GROUP BY rok, miesiac
ORDER BY miesiac, rok;
""")
result = cursor.fetchall()

months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", 
          "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]

data_ilosc_rok = {month: [0, 0, 0] for month in months}

for row in result:
    year, month_number, count = row
    year_index = year - 2022 
    if 0 <= year_index < 3:
        data_ilosc_rok[months[month_number - 1]][year_index] = count

#PYTANIE 3
query = """
SELECT 
  id_rodzaj AS "ID Rodzaju Wycieczki",
  COUNT(DISTINCT CASE WHEN trip_number = 1 THEN id_klienci END) AS "Liczba klientów jako pierwsza",
  COUNT(DISTINCT CASE WHEN trip_number > 1 THEN id_klienci END) AS "Liczba klientów jako kolejna",
  COUNT(DISTINCT CASE WHEN trip_number = max_trip_number THEN id_klienci END) AS "Liczba klientów jako ostatnia"
FROM (
  SELECT 
    k.id_klienci,
    rw.id_rodzaj,
    ROW_NUMBER() OVER (PARTITION BY k.id_klienci ORDER BY r.Data_rezerwacji) AS trip_number,
    COUNT(*) OVER (PARTITION BY k.id_klienci) AS max_trip_number
  FROM Klienci k
  JOIN Rezerwacje r ON k.id_klienci = r.id_klienci
  JOIN Realizowane_wycieczki rw ON r.id_wycieczki = rw.id_wycieczki
) AS TripSequence
GROUP BY id_rodzaj
ORDER BY id_rodzaj;
"""

cursor.execute(query)
results = cursor.fetchall()

dane_druga_ostatnia = []
for row in results:
    id = row[0]
    ile = int(row[1])
    wrocili = int(row[2])
    procent_powroty = round(wrocili / ile* 100, 2)
    ostatnia = int(row[3])
    dane_druga_ostatnia.append((id,ile,wrocili,procent_powroty,ostatnia))


#PYTANIE 4

# Zapytanie SQL dla danych
query = """
SELECT 
    p.id_pracownicy AS IdPracownika,
    CONCAT(p.Imie, ' ', p.Nazwisko) AS Pracownik,
    YEAR(r.Data_rezerwacji) AS Rok,
    SUM(rw.Cena_za_osobe) AS Przychody,
    SUM(
        ko.Nocleg_za_noc * (DATEDIFF(rw.Data_zakonczenia, rw.Data_rozpoczecia) - 2) +
        ko.Przewodnik +
        ko.Loty +
        ko.Atrakcje +
        ko.Ubezpieczenie +
        ko.Transport
    ) AS KosztyOrganizacyjne,
    (
        p.Pensja * 12 + COALESCE(s.Koszt_stanowiska, 0) * 12
    ) AS KosztPracownika,
    SUM(rw.Cena_za_osobe) - 
    (
        p.Pensja * 12 + COALESCE(s.Koszt_stanowiska, 0) * 12
    ) -
    SUM(
        ko.Nocleg_za_noc * (DATEDIFF(rw.Data_zakonczenia, rw.Data_rozpoczecia) - 2) +
        ko.Przewodnik +
        ko.Loty +
        ko.Atrakcje +
        ko.Ubezpieczenie +
        ko.Transport
    ) AS ZyskNetto
FROM 
    Pracownicy p
JOIN 
    Rezerwacje r ON p.id_pracownicy = r.id_pracownicy
JOIN 
    Realizowane_wycieczki rw ON r.id_wycieczki = rw.id_wycieczki
JOIN 
    Koszty_organizacji ko ON rw.id_koszty = ko.id_koszty
LEFT JOIN 
    Stanowisko s ON p.id_stanowisko = s.id_stanowisko
WHERE 
    p.id_pracownicy IN (5, 6, 7)
GROUP BY 
    p.id_pracownicy, Pracownik, Rok
ORDER BY 
    Rok, IdPracownika;
"""

# Wykonanie zapytania SQL
cursor.execute(query)
results = cursor.fetchall()

data_by_year = {}
for row in results:
    id_pracownicy = row[0]  # Używamy id_pracownicy
    rok = row[2]
    przychody = row[3]
    koszty_organizacyjne = row[4]
    zysk_netto = row[6]
    koszt_pracownika = row[5]

    if rok not in data_by_year:
        data_by_year[rok] = []
    data_by_year[rok].append({
        'id_pracownicy': id_pracownicy,  # Używamy id_pracownicy
        'przychody': przychody,
        'koszty_organizacyjne': koszty_organizacyjne,
        'zysk_netto': zysk_netto,
        'koszt_pracownika': koszt_pracownika
    })


#PYTANIE 5

#zliczenie kosztów pracowników z przelicznikiem 1.206 pozwalającym wyliczyć narzut pracodawcy na UoP
cursor.execute("SELECT SUM(Pensja) FROM Pracownicy")
suma_pensja = cursor.fetchone()[0]
if suma_pensja is None:
    narzut = 0

narzut = 1.206*float(suma_pensja)

cursor.execute("SELECT SUM(Koszt_stanowiska) FROM Pracownicy JOIN Stanowisko ON Pracownicy.id_stanowisko = Stanowisko.id_stanowisko")
koszty_stanowiska = cursor.fetchone()[0]
if koszty_stanowiska is None:
    koszty_stanowiska = 0
#miesięczny koszt zatrudnienia pracowników
koszt_pracownicy = narzut + float(koszty_stanowiska)

#Suma kosztów organizacji wycieczek w danym miesiącu
cursor.execute('''
SELECT 
    YEAR(Realizowane_wycieczki.Data_rozpoczecia) AS rok,
    MONTH(Realizowane_wycieczki.Data_rozpoczecia) AS miesiac,
    SUM(
        (Koszty_organizacji.Nocleg_za_noc 
         * (DATEDIFF(Realizowane_wycieczki.Data_zakonczenia, Realizowane_wycieczki.Data_rozpoczecia)-2)
        + Koszty_organizacji.Przewodnik
        + Koszty_organizacji.Loty
        + Koszty_organizacji.Atrakcje
        + Koszty_organizacji.Ubezpieczenie
        + Koszty_organizacji.Transport)
        * (SELECT COUNT(DISTINCT Rezerwacje.id_rezerwacje)
        FROM Rezerwacje 
        WHERE Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
        AND Rezerwacje.id_transakcje IN (SELECT id_transakcje FROM Transakcje_finansowe WHERE Zrealizowano = 1))
    ) AS koszt
FROM Koszty_organizacji 
JOIN Realizowane_wycieczki 
    ON Koszty_organizacji.id_koszty = Realizowane_wycieczki.id_koszty
GROUP BY rok, miesiac
ORDER BY rok, miesiac
LIMIT 34;
''')

wynik = cursor.fetchall()

Koszty_miesiac = []
for row in wynik:
    rok = row[0]
    miesiac = row[1]
    koszt = float(row[2])
    Koszty_miesiac.append((rok,miesiac,koszt))

#Zyski całkowite na miesiąc (po dacie wyjazdu, NIE rezerwacji)
cursor.execute('''
SELECT 
    YEAR(Realizowane_wycieczki.Data_rozpoczecia) AS rok,
    MONTH(Realizowane_wycieczki.Data_rozpoczecia) AS miesiac,
    SUM(Realizowane_wycieczki.Cena_za_osobe 
    * (SELECT COUNT(DISTINCT Rezerwacje.id_rezerwacje)
    FROM Rezerwacje 
    WHERE Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
    AND Rezerwacje.id_transakcje IN (SELECT id_transakcje FROM Transakcje_finansowe WHERE Zrealizowano = 1))
    ) AS przychod
FROM Realizowane_wycieczki
GROUP BY rok, miesiac
ORDER BY rok, miesiac
LIMIT 34;
''')

wynik = cursor.fetchall()
Przychod_miesiac = []
for row in wynik:
    rok = row[0]
    miesiac = row[1]
    przychod = float(row[2])
    Przychod_miesiac.append((rok, miesiac, przychod))



#PYTANIE 6

# Zapytanie SQL do pobrania danych demograficznych klientów według wieku
query = '''
SELECT 
    CASE 
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) < 20 THEN '<20'
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) BETWEEN 20 AND 29 THEN '20-29'
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) BETWEEN 30 AND 39 THEN '30-39'
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) BETWEEN 40 AND 49 THEN '40-49'
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) BETWEEN 50 AND 59 THEN '50-59'
        WHEN YEAR(CURDATE()) - YEAR(Data_urodzenia) BETWEEN 60 AND 69 THEN '60-69'
        ELSE '70+'
    END AS Wiek,
    COUNT(*) AS Liczba
FROM Klienci
JOIN Rezerwacje ON Klienci.id_klienci = Rezerwacje.id_klienci
GROUP BY Wiek;
'''

cursor.execute(query)
results = cursor.fetchall()

# Przygotowanie danych do wykresu
labels_demografia = [row[0] for row in results]
counts_demografia = [row[1] for row in results]

#PYTANIE 7
# Zapytanie SQL do obliczenia średnich ocen dla realizowanych wycieczek
query = '''
SELECT Rodzaje_wycieczek.Nazwa AS Wycieczka, 
       AVG(Oceny.Ocena) AS Srednia_Ocena
FROM Oceny
JOIN Rezerwacje ON Oceny.id_rezerwacje = Rezerwacje.id_rezerwacje
JOIN Realizowane_wycieczki ON Rezerwacje.id_wycieczki = Realizowane_wycieczki.id_wycieczki
JOIN Rodzaje_wycieczek ON Realizowane_wycieczki.id_rodzaj = Rodzaje_wycieczek.id_rodzaj
GROUP BY Rodzaje_wycieczek.Nazwa
ORDER BY Srednia_Ocena DESC;
'''

# Wykonanie zapytania
cursor.execute(query)
results = cursor.fetchall()

# Przygotowanie danych do wykresu
wycieczki_do_ocen = [row[0] for row in results]
srednie_oceny = [row[1] for row in results]


cursor.close()

con.close()

'''
kod do zapisywania generowanych wykresow
plot_filename = "plot.png" //mozna tez .pdf tylko potem wklejac do letexa jako pdf
plt.savefig(plot_filename)
plt.close()
'''



def wykresy1():
    I, L, P, K, Z = [], [], [], [], []
    for i in range(len(Nazwy_wycieczek)):
        indeks , przychod = Suma_przychod[i]
        I.append(indeks)
        P.append(przychod)
        _, koszt = Suma_koszty[i]
        K.append(koszt)
        _, zysk = Zyski_rodzaj[i]
        Z.append(zysk)
        _, osoby = Ilosc_osob[i]
        L.append(osoby)
    
    # Ustawienia wykresu
    x = np.arange(len(I))  # Indeksy dla osi X

    # Tworzenie wykresu słupkowego dla przychodów i kosztów
    plt.figure(figsize=(12, 8))  # Większy wykres
    plt.bar(x - 0.1, P, width=0.2, label='Przychody', align='center', color='#87CEFA')
    plt.bar(x + 0.1, K, width=0.2, label='Koszty', align='center', color='navy')

    # Dodawanie etykiet i tytułu
    plt.xticks(x, I, ha='center', fontsize=10)  # Wyśrodkowanie etykiet
    plt.xlabel("Indeks Wycieczki", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie przychodów i kosztów", fontsize=14)
    plt.legend()
    plt.tight_layout()  # Automatyczne dopasowanie elementów do przestrzeni

    plot_filename = "Wykres_rodzaj_przychody_koszty.png"
    plt.savefig(plot_filename)
    plt.close()

    # Tworzenie wykresu słupkowego dla zysków
    plt.figure(figsize=(12, 8))
    plt.bar(x, Z, width=0.4, label='Zyski_rodzaj', align='center', color='pink')

    plt.xticks(x, I, ha='center', fontsize=10)
    plt.xlabel("Indeks Wycieczki", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie zysków", fontsize=14)
    plt.legend()
    plt.tight_layout()

    plot_filename = "Wykres_rodzaj_zyski.png"
    plt.savefig(plot_filename)
    plt.close()

    # Tworzenie wykresu słupkowego dla ilosci osób
    plt.figure(figsize=(12, 8))
    plt.bar(x, L, width=0.4, label='Ilość rezerwacji', align='center', color='#CC99FF')

    plt.xticks(x, I, ha='center', fontsize=10)
    plt.xlabel("Indeks Wycieczki", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie ilości rezerwacji", fontsize=14)
    plt.legend()
    plt.tight_layout()

    plot_filename = "Wykres_rodzaj_ilosc.png"
    plt.savefig(plot_filename)
    plt.close()


def wykresy2():
    #WYKRESY ZAD 2
    plt.figure(figsize=(10, 6))
    plt.plot(months_liczba_klientow, liczba_klientow, marker='o', color='blue', label='Liczba klientów')
    plt.title('Liczba obsłużonych klientów w każdym miesiącu', fontsize=14)
    plt.xlabel('Miesiąc', fontsize=12)
    plt.ylabel('Liczba klientów', fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig("Liczba_obsluzonych_klientów_w_kazdym_miesiacu.png")
    plt.close()
    #######################################
    plt.figure(figsize=(12, 6))
    plt.bar(data_miesiace['Miesiac'], data_miesiace['Liczba_Osob'], color='skyblue')
    plt.title('Liczba osób na wycieczkach w danym miesiącu (wg daty rozpoczęcia)', fontsize=16)
    plt.xlabel('Miesiąc', fontsize=12)
    plt.ylabel('Liczba osób', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("Liczba_osob_na_wycieczkach_w_danym_miesiacu.png")
    plt.close()
    ###########################################
    plt.bar(data_ilosc_mies.keys(), data_ilosc_mies.values(), color="skyblue")
    plt.title("Liczba osób, które pojechały na wycieczkę w poszczególnych miesiącach")
    plt.xlabel("Miesiąc")
    plt.ylabel("Liczba osób")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("Liczba_osob_które_pojechaly_na_wycieczke_w_poszczegolnych_miesiacach.png")
    plt.close()
    ##########################################
    x = np.arange(len(months)) 
    width = 0.2  

    _, ax = plt.subplots(figsize=(12, 6))
    Kolorki = ["skyblue", "#1E90FF" , "navy"]
    for i, year in enumerate([2022, 2023, 2024]): 
        ax.bar(x + (i - 1) * width, [data_ilosc_rok[month][i] for month in months], width, label=str(year), color = Kolorki[i])

    ax.set_xlabel('Miesiąc')
    ax.set_ylabel('Liczba osób')
    ax.set_title('Liczba osób na wycieczkach w poszczególnych miesiącach w latach 2022-2024')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.legend(title="Rok")

    plt.tight_layout()
    plt.savefig("Liczba_osob_na_wycieczkach_w_poszczegolnych_miesiacach_w_latach_2022_2024.png")
    plt.close()

def wykresy4():
    # Generowanie wykresów dla każdego roku
    for rok, dane in data_by_year.items():
        pracownicy = [entry['id_pracownicy'] for entry in dane]  # Używamy id_pracownicy
        przychody = [entry['przychody'] for entry in dane]
        koszty_organizacyjne = [entry['koszty_organizacyjne'] for entry in dane]
        zyski_netto = [entry['zysk_netto'] for entry in dane]
        koszty_pracownika = [entry['koszt_pracownika'] for entry in dane]

        x = np.arange(len(pracownicy))  # Oś X
        width = 0.2  # Szerokość słupków

        plt.figure(figsize=(12, 6))

        # Dodanie słupków w odpowiedniej kolejności
        plt.bar(x, koszty_organizacyjne, width, label='Koszty Organizacyjne', color="navy")
        plt.bar(x, koszty_pracownika, width, bottom=koszty_organizacyjne, label='Koszt Pracownika', color='#1E90FF')

        # Dodanie słupków przychodów jako osobnych
        plt.bar(x - width, przychody, width, label='Przychody', color='skyblue')

       # Dodanie etykiet i tytułów
        plt.title(f'Porównanie składników finansowych dla pracowników w roku {rok}')
        plt.xlabel('Identyfikator Pracownika')  # Używamy id_pracownicy
        plt.ylabel('Kwota (PLN)')
        plt.xticks(x, pracownicy, rotation=45, ha='right')  # Ustawienie id_pracownicy na osi X
        plt.legend()

        # Zapisanie wykresu
        plot_filename = "Wykres_porownanie_" + str(rok) + ".png"
        plt.savefig(plot_filename)
        plt.close()

        # Dodanie słupków w odpowiedniej kolejności
        plt.bar(x , zyski_netto, width, label='Zysk Netto', color='skyblue')

        # Dodanie etykiet i tytułów
        plt.title(f'Porównanie zysków netto dla pracowników w roku {rok}')
        plt.xlabel('Identyfikator Pracownika')  # Używamy id_pracownicy
        plt.ylabel('Kwota (PLN)')
        plt.xticks(x, pracownicy, rotation=45, ha='right')  # Ustawienie id_pracownicy na osi X
        plt.legend()

        plot_filename = "Wykres_zysk_"+str(rok)+".png"
        plt.savefig(plot_filename)
        plt.close()


Zyski_mies = []
for i in range(len(Koszty_miesiac)):
    rok, miesiac, koszt = Koszty_miesiac[i]
    _,_, przychod = Przychod_miesiac[i]
    zysk = przychod - koszt - koszt_pracownicy
    Zyski_mies.append((rok, miesiac, zysk))

max_zysk_mies = max(Zyski_mies, key = lambda x: x[2])
min_zysk_mies = min(Zyski_mies, key = lambda x: x[2])

def Roczne_przeliczenie():
    koszty_roczne = {}
    przychod_roczny = {}
    zyski_roczne = {}

    for rok, _, koszt in Koszty_miesiac:
        if rok not in koszty_roczne:
            koszty_roczne[rok] = 0
        koszty_roczne[rok] += koszt

    for rok, _, przychod in Przychod_miesiac:
        if rok not in przychod_roczny:
            przychod_roczny[rok] = 0
        przychod_roczny[rok] += przychod

    for rok in koszty_roczne.keys():
        zysk = przychod_roczny[rok] - koszty_roczne[rok] - koszt_pracownicy * 12
        zyski_roczne[rok] = zysk

    Koszty_rok = [koszty_roczne[rok] for rok in sorted(koszty_roczne.keys())]
    Przychod_rok = [przychod_roczny[rok] for rok in sorted(przychod_roczny.keys())]
    Zyski_rok = [zyski_roczne[rok] for rok in sorted(zyski_roczne.keys())]

    return Koszty_rok, Przychod_rok, Zyski_rok

Koszty_rok, Przychod_rok, Zyski_rok = Roczne_przeliczenie()
suma_zysk_rok = round(sum(Zyski_rok))

def wykresy5():
    lata = [2022, 2023, 2024]
    miesiace = [f"{rok}-{str(mies).zfill(2)}" for rok in lata for mies in range(1, 13)]
    del miesiace[0]
    del miesiace[0]

    plt.figure(figsize=(10, 6))
    x = np.arange(len(lata))

    # Tworzenie wykresu słupkowego dla przychodów i kosztów
    plt.figure(figsize=(12, 8))
    plt.bar(x - 0.1, Przychod_rok, width=0.2, label='Przychody', align='center', color='#87CEFA')
    plt.bar(x + 0.1, Koszty_rok, width=0.2, label='Koszty', align='center', color='navy')

    plt.xticks(x, lata, ha='center', fontsize=10)
    plt.xlabel("Rok", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie przychodów i kosztów", fontsize=14)
    plt.legend()
    plt.tight_layout()

    plot_filename = "Wykres_roczne_koszty_przychody.png"
    plt.savefig(plot_filename)
    plt.close()

    # Tworzenie wykresu słupkowego dla zysków
    plt.figure(figsize=(12, 8))
    plt.bar(x , Zyski_rok, width=0.2, label='Zysk', align='center', color='pink')

    plt.xticks(x, lata, ha='center', fontsize=10)
    plt.xlabel("Rok", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie zysków", fontsize=14)
    plt.legend()
    plt.tight_layout()

    plot_filename = "Wykres_roczne_zyski.png"
    plt.savefig(plot_filename)
    plt.close()

    koszty_mies = [row[2] for row in Koszty_miesiac]
    przychod_mies = [row[2] for row in Przychod_miesiac]
    zyski_mies = [zysk[2] for zysk in Zyski_mies]

    assert len(miesiace) == len(koszty_mies), f"Length mismatch: {len(miesiace)} != {len(koszty_mies)}"
    assert len(miesiace) == len(przychod_mies), f"Length mismatch: {len(miesiace)} != {len(przychod_mies)}"
    assert len(miesiace) == len(zyski_mies), f"Length mismatch: {len(miesiace)} != {len(zyski_mies)}"

    x = np.arange(len(miesiace))
    # koszty i przychody mies
    plt.figure(figsize=(18, 10))
    plt.bar(x - 0.2, przychod_mies, width=0.4, label="Przychody", color="#87CEFA")
    plt.bar(x + 0.2, koszty_mies, width=0.4, label="Koszty", color="navy")

    plt.xticks(x, miesiace, rotation = 45, ha="center", fontsize=8)
    plt.xlabel("Miesiąc", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie przychodów i kosztów miesięcznych", fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.savefig("wykres_miesieczne_przychody_koszty.png")
    plt.close()

    #zysk mies
    plt.figure(figsize=(18, 10))
    plt.bar(x, zyski_mies, width=0.6, label="Zysk", color="pink")

    plt.xticks(x, miesiace, rotation = 45, ha="center", fontsize=8)
    plt.xlabel("Miesiąc", fontsize=12)
    plt.ylabel("Wartość", fontsize=12)
    plt.title("Porównanie zysków miesięcznych", fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.savefig("wykres_miesieczne_zyski.png")
    plt.close()


def wykresy6():
    # Tworzenie wykresu kołowego
    plt.figure(figsize=(8, 8))
    plt.pie(counts_demografia, labels=labels_demografia, autopct='%1.1f%%', colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6', '#d9b3ff'], startangle=140)
    plt.title('Demografia klientów według wieku', fontsize=14, fontweight='bold')
    plt.axis('equal')

    # Zapisanie wykresu
    plot_filename = "Demografia_wiekowa.png"
    plt.savefig(plot_filename)
    plt.close()


def wykresy7():
    # Generowanie pastelowych kolorów dla słupków
    kolory = plt.cm.Set2(np.linspace(0, 1, len(wycieczki_do_ocen)))
    kolory[0] = np.array([1, 0.6, 0.6, 1])  
    kolory[-1] = np.array([0.7, 0.4, 1, 1])  

    # Tworzenie wykresu
    plt.figure(figsize=(10, 6))
    plt.barh(wycieczki_do_ocen, srednie_oceny, color=kolory)
    plt.xlabel('Średnia Ocena', fontweight='bold', fontsize=12)
    plt.ylabel('Rodzaj wycieczki', fontweight='bold', fontsize=12)
    plt.title('Średnie Oceny Wycieczek', fontsize=16, fontweight='bold', loc='center')
    plt.gca().invert_yaxis()  
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plot_filename = "Oceny.png"
    plt.savefig(plot_filename)
    plt.close()

wykresy1()
wykresy2()
wykresy4()
wykresy5()
wykresy6()
wykresy7()

# Funkcja generująca raport LaTeX
def generuj_raport(plik_wyjsciowy="Raport"):
    # Tworzenie dokumentu LaTeX
    doc = Document()

    doc.preamble.append(NoEscape(r'\usepackage[T1]{fontenc}'))
    doc.preamble.append(NoEscape(r'\usepackage[utf8]{inputenc}'))
    doc.preamble.append(NoEscape(r'\usepackage[polish]{babel}'))
    doc.preamble.append(NoEscape(r'\usepackage{graphicx}'))
    doc.preamble.append(NoEscape(r'\usepackage{amsmath, amsthm, amssymb}'))
    doc.preamble.append(NoEscape(r'\usepackage{hyperref}'))
    doc.preamble.append(NoEscape(r'\usepackage{booktabs}'))
    
    # Tytuł, autorzy, data
    doc.preamble.append(Command('title', 'RAPORT'))
    doc.preamble.append(Command('author', NoEscape(
    r"""Amelia Dorożko, 282259 \\ 
    Matylda Mordal, 282240 \\ 
    Zuzanna Pawlik, 282230 \\ 
    Paweł Solecki, 282246 \\ 
    Zofia Stępień, 282254""")))
    doc.preamble.append(Command('date', '30.01.2025'))
    
    # Początek dokumentu
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(rf'''
\section*{{Wstęp}}
Tutaj można wrzucic jakiś krótki opis w stylu\\
poniżej znajdują się pytania z analizy oraz odpowiedzi na nie w formie tabel, wykresów + wnioski\\
dodatkowo możemy tutaj dać listę założeń ogólnych, a założenia do konkretnych pyatń dawać już bezpośrednio
przed wykresami/tabelami

\section*{{Pytanie 1}}
Znajdź najpopularniejsze rodzaje wycieczek, porównaj koszta i zyski, czy są opłacalne?\\
\\
                        '''))
    with doc.create(Subsection("Rodzaje Wycieczek", numbering=False)):
        with doc.create(Tabular('|c|l|')) as table:
            table.add_hline()
            table.add_row(("id_rodzaj", "Nazwa"))
            table.add_hline()
            for id_rodzaj, nazwa in Nazwy_wycieczek:
                table.add_row((id_rodzaj, nazwa))
                table.add_hline()

    doc.append(NoEscape(rf'''
\subsection*{{Wykresy do pytania 1}}

Ilość osób na danej wycieczce

\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_rodzaj_ilosc.png}}
\end{{center}}                      

Porównanie przychodów i kosztów

\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_rodzaj_przychody_koszty}}
\end{{center}}                       
                        
Porównanie zysków

\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_rodzaj_zyski.png}}
\end{{center}}
'''))
 
    doc.append(NoEscape(rf"""
\subsubsection*{{Wycieczki z największym i najmniejszym zyskiem}}

Wycieczka o największym zysku:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {max_zysk_rodzaj[0]}
    \item \textbf{{Zysk:}} {max_zysk_rodzaj[1]:,.2f} PLN
\end{{itemize}}
Wycieczka o najmniejszym zysku:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {min_zysk_rodzaj[0]}
    \item \textbf{{Zysk:}} {min_zysk_rodzaj[1]:,.2f} PLN
\end{{itemize}}
"""))
    
    najlepszy_rez = max(miesiac_rez, key=lambda x: x[1])
    najgorszy_rez = min(miesiac_rez, key=lambda x: x[1])

    najlepszy_mies_wyjazd = max(wyjazdy_na_miesiac, key = lambda x: x[1])
    najgorszy_mies_wyjazd = min(wyjazdy_na_miesiac, key = lambda x: x[1])

    najlepszy_ilosc_rok = max(suma_ilosc_rok, key = lambda x: x[1])
    najgorszy_ilosc_rok = min(suma_ilosc_rok, key = lambda x: x[1])



    doc.append(NoEscape(rf"""
\section*{{Pytanie 2}}
Sporządź wykres liczby obsłużonych klientów w każdym miesiącu działalności firmy, czy firma rośnie, czy podupada?

\subsubsection*{{Ilość osób, które złożyły rezerwację w danym miesiącu}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Liczba_obsluzonych_klientów_w_kazdym_miesiacu.png}}
\end{{center}}
Miesiąc z największą ilością rezerwacji:
\begin{{itemize}}
    \item \textbf{{Miesiąc: }} {najlepszy_rez[0]}
    \item \textbf{{Ilość rezerwacji}} {najlepszy_rez[1]}
\end{{itemize}}
Miesiąc z najmniejszą ilością rezerwacji:
\begin{{itemize}}
    \item \textbf{{Miesiąc: }} {najgorszy_rez[0]}
    \item \textbf{{Ilość rezerwacji}} {najgorszy_rez[1]}
\end{{itemize}} 

\subsubsection*{{Ilość osób, które pojechały na wycieczkę w danym miesiącu}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Liczba_osob_na_wycieczkach_w_danym_miesiacu.png}}
\end{{center}}
Miesiąc z największą ilością wyjazdów:
\begin{{itemize}}
    \item \textbf{{Miesiąc: }} {najlepszy_mies_wyjazd[0]}
    \item \textbf{{Ilość rezerwacji}} {najlepszy_mies_wyjazd[1]}
\end{{itemize}}
Miesiąc z najmniejszą ilością wyjazdów:
\begin{{itemize}}
    \item \textbf{{Miesiąc: }} {najgorszy_mies_wyjazd[0]}
    \item \textbf{{Ilość rezerwacji}} {najgorszy_mies_wyjazd[1]}
\end{{itemize}} 

\subsubsection*{{Ilość osób, które pojechały na wycieczkę w danym miesiącu - porównanie względem roku}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Liczba_osob_na_wycieczkach_w_poszczegolnych_miesiacach_w_latach_2022_2024.png}}
\end{{center}}
Rok z największą ilością klientów na wyjazdach:
\begin{{itemize}}
    \item \textbf{{Rok: }} {najlepszy_ilosc_rok[0]}
    \item \textbf{{Ilość osób na wyjazdach: }} {najlepszy_ilosc_rok[1]}
\end{{itemize}}
Rok z najmniejszą ilością klientów na wyjazdach:
\begin{{itemize}}
    \item \textbf{{Rok: }} {najgorszy_ilosc_rok[0]}
    \item \textbf{{Ilość osób na wyjazdach: }} {najgorszy_ilosc_rok[1]}
\end{{itemize}} 

\subsubsection*{{Porównanie popularności wycieczek ze względu na miesiąc rozpoczęcia}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Liczba_osob_które_pojechaly_na_wycieczke_w_poszczegolnych_miesiacach.png}}
\end{{center}}



\section*{{Pytanie 3}}
Sprawdź, po których wycieczkach klienci wracają na kolejne, a po których mają dość i więcej ich nie widzicie. Czy są takie, które być może powinny zniknąć z oferty?

\subsection*{{Tabela danych}}
"""))
    with doc.create(Center()):
        with doc.create(Tabular('|c|c|c|c|c|')) as table:
            table.add_hline()
            table.add_row(("Id wycieczki", "Pierwsza wycieczka", "Kolejna wycieczka","Odsetek powrotów" , "Ostatnia wycieczka"))
            table.add_hline()
            for i,a,b,c,d in dane_druga_ostatnia:
                table.add_row((i,a,b,str(c)+'%',d))
                table.add_hline()

    max_powroty = max(dane_druga_ostatnia, key = lambda x: x[3])
    min_powroty = min(dane_druga_ostatnia, key = lambda x: x[3])

    posortowane_po_ost = sorted(dane_druga_ostatnia, key=lambda x: x[4])
    id_best = posortowane_po_ost[0][0]
    id_worst = posortowane_po_ost[-1][0]


    doc.append(NoEscape(rf"""Pierwsza wycieczka - Ile osób było na tej wycieczce jako na swojej pierwszej
Kolejna wycieczka - Ile z tych osób wybrało się na kolejną wycieczkę
Odsetek powrotów - Jaką część stanowią osoby, które wybrały się na kolejną wycieczkę
Ostatnia wycieczka - Ile osób po danej wycieczce nie było już na żadnej innej
\subsubsection*{{Wycieczki z największym i najmniejszym odsetkiem powrotów}}

Wycieczka o największym odsetku powrotów:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {max_powroty[0]}
    \item \textbf{{Odsetek powrotów: }} {max_powroty[3]}\%
\end{{itemize}}
Wycieczka o najmniejszym odsetku powrotów:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {min_powroty[0]}
    \item \textbf{{Odsetek powrotów}} {min_powroty[3]}\%
\end{{itemize}}

\subsubsection*{{Wycieczki po których nie wraca najmniej i najwięcej klientów}}

Wycieczka, po której nie wraca najmniej osób:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {id_best}
\end{{itemize}}
Wycieczka, po której nie wraca najwięcej osób:
\begin{{itemize}}
    \item \textbf{{id rodzaju:}} {id_worst}
\end{{itemize}}

\subsection*{{Wykresy do zadania 4}}

\subsubsection*{{2022}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_porownanie_2022.png}}
\end{{center}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_zysk_2022.png}}
\end{{center}}

\subsubsection*{{2023}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_porownanie_2023.png}}
\end{{center}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_zysk_2023.png}}
\end{{center}}

\subsubsection*{{2024}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_porownanie_2024.png}}
\end{{center}}
\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_zysk_2024.png}}
\end{{center}}

\subsection*{{Wykresy do zadania 5}}
\subsubsection*{{Porównanie miesięczne}}

Przychody i koszty

\begin{{center}}
\includegraphics[width = \textwidth]{{wykres_miesieczne_przychody_koszty.png}}
\end{{center}}

Zyski

\begin{{center}}
\includegraphics[width = \textwidth]{{wykres_miesieczne_zyski.png}}
\end{{center}}
Miesiąc o największym zysku:
\begin{{itemize}}
    \item \textbf{{Rok}} {max_zysk_mies[0]}
    \item \textbf{{Miesiąc}} {max_zysk_mies[1]}
    \item \textbf{{Zysk:}} {max_zysk_mies[2]:,.2f} PLN
\end{{itemize}}
Miesiąc o najmniejszym zysku:
\begin{{itemize}}
    \item \textbf{{Rok}} {min_zysk_mies[0]}
    \item \textbf{{Miesiąc}} {min_zysk_mies[1]}
    \item \textbf{{Zysk:}} {min_zysk_mies[2]:,.2f} PLN
\end{{itemize}}

\subsubsection*{{Porównanie roczne}}

Przychody i koszty

\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_roczne_koszty_przychody.png}}
\end{{center}}

Zyski

\begin{{center}}
\includegraphics[width = \textwidth]{{Wykres_roczne_zyski.png}}
\end{{center}}

\begin{{itemize}}
    \item \textbf{{Zysk całkowity}} {suma_zysk_rok} PLN
\end{{itemize}}

\subsection*{{Wykres do zadania 6}}

\begin{{center}}
\includegraphics[width = \textwidth]{{Demografia_wiekowa.png}}
\end{{center}}

\subsection*{{Wykres do zadania 7}}

\begin{{center}}
\includegraphics[width = \textwidth]{{Oceny.png}}
\end{{center}}

\end{{document}}
"""))
    
    doc.generate_tex(plik_wyjsciowy)
    print(f"Raport zapisano jako {plik_wyjsciowy}.tex")


generuj_raport()
try:
    subprocess.run(["pdflatex", 'Raport.tex'], check=True)
    print("Raport wygenerowany pomyślnie.")
except FileNotFoundError:
    print("Nie znaleziono programu pdflatex. Upewnij się, że LaTeX jest zainstalowany.")
except subprocess.CalledProcessError as e:
    print("Błąd podczas kompilacji LaTeX:", e)