import csv

with open('club.csv', 'r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file, delimiter=';')
    
    print("Noms des colonnes :")
    for i, col in enumerate(reader.fieldnames, 1):
        print(f"{i}. '{col}'")
    
    print("\n" + "="*50)
    print("Première ligne de données :")
    
    for row in reader:
        for key, value in row.items():
            print(f"{key}: {value}")
        break