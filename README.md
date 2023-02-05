### Сбор данных с сайта объявлений об аренде и продаже недвижимости Циан

Cianparser - это библиотека Python 3 (версии 3.8 и выше) для парсинга сайта  [Циан](http://cian.ru).
С его помощью можно получить достаточно подробные и структурированные данные по краткосрочной и долгосрочной аренде, продаже квартир, домов, танхаусов итд.

### Установка
```bash
pip install cianparser
```

### Использование
```python
import cianparser
    
data = cianparser.parse(
    deal_type="rent_long",
    accommodation_type="flat",
    location="Москва",
    rooms=(2, 3),
    start_page=1,
    end_page=2,
    is_saving_csv=True,
    is_latin=False,
    is_express_mode=False,
    is_by_homeowner=False,
)

print(data[0])
```

```
                              Preparing to collect information from pages..

The absolute path to the file: 
 /Users/macbook/some_project/cian_parsing_result_rent_long_1_2_moskva_04_Feb_2023_06_58_21_765479.csv 

The page from which the collection of information begins: 
 https://cian.ru/cat.php?engine_version=2&p=1&region=1&offer_type=flat&deal_type=rent&room2=1&room3=1&with_neighbors=0&type=4 

Collecting information from pages with list of announcements
1 | 1 page with list: [=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>] 100% | Count of parsed: 28. Progress ratio  50 %. Average price: 204 642 rub
2 | 2 page with list: [=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>] 100% | Count of parsed: 56. Progress ratio 100 %. Average price: 236 426 rub

{  'accommodation_type': 'flat',
   'deal_type': 'rent',
   'city': 'Москва',
   'district': 'Замоскворечье',
   'underground': 'Новокузнецкая',
   'street': 'Космодамианская набережная',
   'floor': 5,
   'floors_count': 12,
   'total_meters': 85.0,
   'living_meters': 55.0,
   'kitchen_meters': 11.0,
   'rooms_count': 3,
   'year_of_construction': '1954',
   'price_per_month': 93000,
   'price_per_m2': 1094,
   'commissions': 50,
   'author': 'Apple Real Estate',
   'author_type': 'real_estate_agent',
   'phone': '+79057145354',
   'link': 'https://www.cian.ru/rent/flat/282487326/',
}

The collection of information from the pages with list of announcements is completed
Total number of parced announcements: 56. Average price per month: 236 426 rub
```

### Конфигурация
Функция __*parse*__ имеет следующий аргументы:
* __deal_type__ - тип объявления, к примеру, долгосрочная, краткосрочная аренда, продажа _("rent_long", "rent_short", "sale")_
* __accommodation_type__ - вид жилья, к примеру, квартира, комната, дом, часть дома, таунхаус _("flat", "room", "house", "house-part", "townhouse")_
* __location__ - локация объявления, к примеру, Казань (для просмотра доступных мест используйте _cianparser.list_cities())_
* __rooms__ - количество комнат, к примеру, _1, (1,3, "studio"), "studio, "all"_; по умолчанию любое _("all")_
* __start_page__ - страница, с которого начинается сбор данных, по умолчанию, _1_
* __end_page__ - страница, с которого заканчивается сбор данных, по умолчанию, _100_
* __is_saving_csv__ - необходимо ли сохранение собираемых данных (в реальном времени в процессе сбора данных) или нет, по умолчанию _False_
* __is_latin__ - необходимо ли преобразывание любой встрещающейся __кириллицы__ в __латиницу__, по умолчанию _False_
* __is_express_mode__ - необходимо ли <ins>ускорение</ins> (___в 5-10 раз___) сбор данных (<ins>__но без трех полей__</ins>, см примечание), по умолчанию _False_
* __is_by_homeowner__ - необходимо ли собирать данные с объявлений, созданных только собственниками, по умолчанию _False_

Если имеется желание __собрать данные со всех страниц__, то можно пропустить аргумент __start_page__ и указать значение __end_page__ достаточно большим (к примеру, _100000_).
В проекте предусмотрен функционал корректного завершения в случае окончания страниц

#### В настоящее время функционал доступен только по продажам (sale) и долгосрочном арендам (rent_long) квартир и студий (flat).

### Признаки, получаемые в ходе сбора данных с предложений по долгосрочной аренде недвижимости
* __district__ - район
* __underground__ - метро
* __street__ - улица
* __floor__ - этаж
* __floors_count__ - общее количество этажей
* __total_meters__ - общая площадь
* __living_meters__ - жилая площади
* __kitchen_meters__ - площадь кухни
* __rooms_count__ - количество комнат
* __year_construction__ - год постройки здания
* __price_per_month__ - стоимость в месяц
* __price_per_m2__ - стоимость на квадратный метр
* __commissions__ - комиссия, взымаемая при заселении
* __author__ - автор объявления
* __author_type__ - тип автора 
* __phone__ - номер телефона в объявлении
* __link__ - ссылка на объявление

Возможные значения поля __author_type__:
- __real_estate_agent__ - агентство недвижимости
- __homeowner__ - собственник
- __realtor__ - риелтор
- __official_representative__ - ук оф.представитель
- __representative_developer__ - представитель застройщика
- __developer__ - застройщик
- __unknown__ - без указанного типа

### Признаки, получаемые в ходе сбора данных с предложений по продаже недвижимости

Признаки __аналогичны__ вышеописанным, кроме отсутствия полей __price_per_month__ и __commissions__.

При этом появляются новые:
* __price__ - стоимость недвижимости
* __residential_complex__ - название жилого комплекса

### Сохранение данных
Имеется возможность сохранения собираемых данных в режиме реального времени. Для этого необходимо подставить в аргументе 
__is_saving_csv__ значение ___True___.

Пример получаемого файла:

```bash
cian_parsing_result_rent_long_1_2_moskva_04_Feb_2023_06_58_21_765479.csv
```

| author | author_type | link | city | deal_type | accommodation_type | floor | floors_count | rooms_count | total_meters | price_per_month | price_per_m2 | commissions | year_of_construction | living_meters | kitchen_meters | phone | district | street | underground
| ------ | ----------- | ---- | ---- | --------- | ------------------ | ----- | ------------ | ----------- | ------------ | --------------- | ----------- | ----------- | -------------------- | --- | --- | --- | --- | --- | ---
| Intermark Real Estate | real_estate_agent | https://www.cian.ru/rent/flat/278903117/ | Москва | rent | flat | 4 | 6 | 3 | 50.0 | 180000 | 3600 | 0 | 1911 | 32.0 | 8.0 | +79676513428 | Пресненский | Малый Предтеченский переулок | Краснопресненская
| Capital Mars | real_estate_agent | https://www.cian.ru/rent/flat/282506328/ | Москва | rent | flat | 5 | 9 | 2 | 89.0 | 180000 | 2022 | 0 | 2006 | 53.0 | 15.0 | +79660619653 | Хамовники | 3-я Фрунзенская | Спортивная
| MERSI | real_estate_agent | https://www.cian.ru/rent/flat/281562376/ | Москва | rent | flat | 8 | 16 | 2 | 80.0 | 200000 | 2500 | 0 | 2012 | -1 | -1 | +79652455850 | Замоскворечье | Мытная | Октябрьская

### Ограничение
Сайт выдает страницы со списком объявлений <ins>__лишь до 54 странцы включительно__</ins>. Это примерно _28*54 = 1512_.
Поэтому имеется рекомендация использовать более конкретные запросы (по количеству комнат). 

К примеру, вместо того чтобы при использовании указывать _rooms=(1, 2)_, стоит два раза отдельно собирать данные с параметроми _rooms=1_ и _rooms=2_ соответственно

### Примечание
1. В некоторых объявлениях отсутсвуют данные по некоторым признакам (_год постройки, жилые кв метры, кв метры кухни итп_).
В этом случае проставляется значение ___-1___ либо ___пустая строка___ для числового и строкового типа поля соответственно.

2. Для отсутствия блокировки по __IP__ в данном проекте задана пауза (___в размере 4-5 секунд___) после сбора информации с
каждой отдельной взятой страницы.

3. Имеется флаг __is_express_mode__, при помощи которого можно существенно (___в 5-10 раз___) ускорить сбор данных благодаря отсутствию необходимости 
заходить на каждую страницу с предложением. 
Однако в таком случае <ins>__не будут__</ins> собираться данные о ___площади кухни___, ___годе постройки здания___ и ___номере телефона___.

4. Данный парсер не будет работать в таком инструменте как [Google Colaboratory](https://colab.research.google.com/). 
См. [подробности](https://github.com/lenarsaitov/cianparser/issues/1)
