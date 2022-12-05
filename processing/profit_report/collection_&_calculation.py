import pandas as pd
from os import walk

# костыль c ISO, можно будет убрать, когда кампании будут называться по кодам
# кинь его в папку с этим ноутбуком
iso = pd.read_excel('fff.xlsx')[['РУССКОЕ НАЗВАНИЕ', 'A2']]
iso['РУССКОЕ НАЗВАНИЕ'] = iso['РУССКОЕ НАЗВАНИЕ'].replace('Пуэрто‐Рико', 'ПуэртоРико')
iso['РУССКОЕ НАЗВАНИЕ'] = iso['РУССКОЕ НАЗВАНИЕ'].replace('Коста‐Рика', 'КостаРика')
# тут забавная чепуха - replace не мог заменить "-" на ""

# функция для замен в spend под формат ISO, если появятся страны с "-", скорее всего придется добавить сюда по аналогии
def for_iso(df):
    df['Название страны'] = df['Название страны'].replace('США', 'Соединенные Штаты Америки')
    df['Название страны'] = df['Название страны'].replace('Киргизия', 'Киргизстан')
    df['Название страны'] = df['Название страны'].replace('Пуэрто-Рико', 'ПуэртоРико')
    df['Название страны'] = df['Название страны'].replace('Коста-Рика', 'КостаРика')
    df['Название страны'] = df['Название страны'].replace('ОАЭ', 'Объединенные Арабские Эмираты')
    return df

# для revenue
def rev_corr(rev):
    rev = rev.drop(columns={'Учтено (пока для отладки CPL)', 'Cost/CPL (In development)'})
    rev['Total_revenue'] = rev.drop(columns={'Group By', 'Install'}).max(axis=1)
    rev_corrected = rev[['Group By','Install', 'Total_revenue']]
    rev_corrected['Group By'] = rev_corrected['Group By'].astype(str)
    return rev_corrected

# расчеты
def what_we_want(spend, revenue):
    spend.columns = ['Campaign ID', 'Conversions', 'Cost']
    spend['Campaign ID'] = spend['Campaign ID'].astype(str)
    
    total = spend.merge(revenue, how='left', left_on='Campaign ID', right_on='Group By')
    total.drop(columns = {'Group By'}, inplace=True)

    total['CR_from_install'] = total['Conversions'] / total['Install']
    total['Profit'] = total['Total_revenue'] - total['Cost']
    total['LTV'] = total['Total_revenue'] / total['Conversions']
    return total

# путь к папке, где лежат твои папочки со spends & revenues через "/" (на винде "\\")
path = 'C:/Users/AM/DATA_ANALYST/tests and so/Dudos/TA/revenue_and_spend'

# для трех сеток, новые можно дописать
for current_path, directs, files in walk(path):
    for file in files:
        # создаем полный путь к файлу
        data_path = (f'{current_path}/{file}')
        print(data_path)
        # читаем данные
        if file.split('.')[0].lower() == "revenue":
            try:
                revenue = pd.read_excel(data_path)
            except:
                revenue = pd.read_csv(data_path)
            
            revenue = rev_corr(revenue)
            rev_direct = current_path.split('/')[:-1]
            break
            
        elif file.split('.')[0].lower() == "spend":
            try:
                spend = pd.read_excel(data_path)
            except:
                spend = pd.read_csv(data_path)
            spend_direct = current_path.split('/')[:-1]

        else:
            print(f'Кто-то ошибся и выгрузил что-то не то, проблема с {data_path}')

        # ну и понеслась
        if rev_direct == spend_direct and spend.columns[0] == 'Campaign ID':
            spend = spend[['Campaign ID', 'Conversions', 'Cost']]
            
        elif rev_direct == spend_direct and spend.columns[0] == 'Название страны':
            spend = for_iso(spend)
            spend = (
                    spend
                    .merge(iso, how = 'left', left_on='Название страны', right_on='РУССКОЕ НАЗВАНИЕ')
                    [['A2', 'Конверсий', 'Потрачено']]
                    )
            
        elif rev_direct == spend_direct and spend.columns[0] == 'Zone ID':
            spend = (
                    spend
                    [['Zone ID', 'Conversions', 'Cost']]
                    )
            spend['Zone ID'] = spend['Zone ID'].fillna(0).astype(int)
            
        else:
            continue
        
        total = what_we_want(spend, revenue)
        total.to_csv(f'total_{rev_direct[-1]}.csv', sep=',') # сохраняет csv с именем сетки в папку со скриптом
        
        print('Вроде ок')
