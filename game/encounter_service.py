import random
from game.type_service import TYPE_LABELS
from database.repositories import register_monster_seen, get_damage_multiplier, render_type_hint

DISTRICT_POOLS = {

"elite_forest": {
    "monsters": [
        {"name": "Чащобный альфа", "rarity": "epic", "mood": "fear", "monster_type": "nature", "weight": 18},
        {"name": "Шёпот кроны", "rarity": "epic", "mood": "inspiration", "monster_type": "echo", "weight": 14},
        {"name": "Корнепасть", "rarity": "legendary", "mood": "rage", "monster_type": "nature", "weight": 8},
        {"name": "Хранитель старого дуба", "rarity": "legendary", "mood": "fear", "monster_type": "bone", "weight": 6}
    ],
    "events": [
        {"type": "cache", "text": "Под древним корнем спрятан трофей охотников.", "weight": 10},
        {"type": "anomaly", "text": "Лес затихает так резко, будто сам наблюдает за тобой.", "weight": 12}
    ]
},
"elite_hills": {
    "monsters": [
        {"name": "Хребтовый колун", "rarity": "epic", "mood": "instinct", "monster_type": "bone", "weight": 18},
        {"name": "Синий разрушитель", "rarity": "epic", "mood": "rage", "monster_type": "storm", "weight": 12},
        {"name": "Старший монолит", "rarity": "legendary", "mood": "instinct", "monster_type": "bone", "weight": 8},
        {"name": "Глас разлома", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 6}
    ],
    "events": [
        {"type": "cache", "text": "Ты находишь редкий геологический схрон.", "weight": 10},
        {"type": "rift", "text": "Разлом в скале мерцает изнутри холодным светом.", "weight": 8}
    ]
},
"elite_marsh": {
    "monsters": [
        {"name": "Топный ловчий", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 18},
        {"name": "Смоляной жрец", "rarity": "epic", "mood": "fear", "monster_type": "void", "weight": 12},
        {"name": "Болотный владыка", "rarity": "legendary", "mood": "fear", "monster_type": "shadow", "weight": 8},
        {"name": "Омутный архив", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 5}
    ],
    "events": [
        {"type": "trail", "text": "По вязкой воде тянется след огромного существа.", "weight": 10},
        {"type": "anomaly", "text": "Болото словно дышит. Из глубины доносится гул.", "weight": 10}
    ]
},

"legend_fields": {
    "monsters": [
        {"name":"Златорогий олень","rarity":"legendary","mood":"inspiration","monster_type":"nature","weight":5},
        {"name":"Луговой титан","rarity":"legendary","mood":"instinct","monster_type":"bone","weight":4},
        {"name":"Световой пастух","rarity":"epic","mood":"inspiration","monster_type":"echo","weight":8},
        {"name":"Песнь ветров","rarity":"epic","mood":"inspiration","monster_type":"storm","weight":7}
    ],
    "events":[
        {"type":"anomaly","text":"Трава светится мягким золотым светом.","weight":10},
        {"type":"trail","text":"Следы огромного существа уходят за холм.","weight":8}
    ]
},
"ancient_hills": {
    "monsters":[
        {"name":"Каменный великан","rarity":"legendary","mood":"rage","monster_type":"bone","weight":5},
        {"name":"Живой монолит","rarity":"epic","mood":"instinct","monster_type":"bone","weight":9},
        {"name":"Кристальный дух","rarity":"rare","mood":"inspiration","monster_type":"storm","weight":12},
        {"name":"Гранитный зверь","rarity":"rare","mood":"rage","monster_type":"bone","weight":11}
    ],
    "events":[
        {"type":"anomaly","text":"Камни вокруг вибрируют.","weight":12},
        {"type":"cache","text":"Ты находишь тайник шахтёров.","weight":9}
    ]
},


"wind_garden": {
    "monsters": [
        {"name": "Ветряной заяц", "rarity": "common", "mood": "inspiration", "monster_type": "storm", "weight": 25},
        {"name": "Листовой певун", "rarity": "rare", "mood": "inspiration", "monster_type": "echo", "weight": 18},
        {"name": "Садовый каратель", "rarity": "epic", "mood": "rage", "monster_type": "nature", "weight": 10},
        {"name": "Небесный пастух", "rarity": "legendary", "mood": "inspiration", "monster_type": "storm", "weight": 5},
    ],
    "events": [
        {"type": "trail", "text": "Порывы ветра складываются в путь между травами.", "weight": 10},
        {"type": "anomaly", "text": "Воздух звенит, будто в нём натянута невидимая струна.", "weight": 10},
    ],
},
"crystal_shelf": {
    "monsters": [
        {"name": "Кристальный страж", "rarity": "rare", "mood": "inspiration", "monster_type": "storm", "weight": 18},
        {"name": "Осколочный хищник", "rarity": "epic", "mood": "rage", "monster_type": "bone", "weight": 12},
        {"name": "Синяя жила", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 5},
    ],
    "events": [
        {"type": "cache", "text": "Между кристаллами блестит редкая находка.", "weight": 12},
        {"type": "rift", "text": "Свет в кристаллах ломается так, словно за ними скрыт другой мир.", "weight": 7},
    ],
},
"reed_maze": {
    "monsters": [
        {"name": "Камышовый резчик", "rarity": "rare", "mood": "fear", "monster_type": "shadow", "weight": 18},
        {"name": "Тростниковый глаз", "rarity": "epic", "mood": "fear", "monster_type": "echo", "weight": 10},
        {"name": "Смотритель топей", "rarity": "legendary", "mood": "fear", "monster_type": "void", "weight": 5},
    ],
    "events": [
        {"type": "trail", "text": "Камыши расступаются и тут же смыкаются за твоей спиной.", "weight": 10},
        {"type": "anomaly", "text": "Кто-то шепчет из зарослей, но рядом никого нет.", "weight": 10},
    ],
},

"green_meadow": {
    "monsters": [
        {"name": "Луговой прыгун", "rarity": "common", "mood": "inspiration", "monster_type": "nature", "weight": 25},
        {"name": "Светлый мотылёк", "rarity": "common", "mood": "inspiration", "monster_type": "echo", "weight": 20},
        {"name": "Травяной сторож", "rarity": "rare", "mood": "instinct", "monster_type": "nature", "weight": 15},
        {"name": "Росный пастух", "rarity": "rare", "mood": "inspiration", "monster_type": "spirit", "weight": 12},
        {"name": "Жемчужный кузнечик", "rarity": "rare", "mood": "instinct", "monster_type": "storm", "weight": 10},
        {"name": "Эхо-перепел", "rarity": "epic", "mood": "inspiration", "monster_type": "echo", "weight": 7},
        {"name": "Страж лугов", "rarity": "epic", "mood": "instinct", "monster_type": "bone", "weight": 6},
        {"name": "Солнечный хищник", "rarity": "legendary", "mood": "rage", "monster_type": "flame", "weight": 5},
    ],
    "events": [
        {"type": "anomaly", "text": "Трава ложится кругом, будто невидимое существо только что прошло здесь.", "weight": 12},
        {"type": "cache", "text": "В траве спрятан забытый мешочек с мелочами путешественника.", "weight": 10},
        {"type": "trail", "text": "Ты замечаешь цепочку свежих следов, ведущих к редкому существу.", "weight": 8},
    ],
},
"flower_valley": {
    "monsters": [
        {"name": "Пыльцевой дух", "rarity": "common", "mood": "inspiration", "monster_type": "spirit", "weight": 24},
        {"name": "Лепестковый лис", "rarity": "rare", "mood": "inspiration", "monster_type": "nature", "weight": 18},
        {"name": "Медовый шёпот", "rarity": "rare", "mood": "inspiration", "monster_type": "echo", "weight": 15},
        {"name": "Садовый страж", "rarity": "rare", "mood": "instinct", "monster_type": "nature", "weight": 12},
        {"name": "Полевой змеец", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 10},
        {"name": "Венец рассвета", "rarity": "epic", "mood": "inspiration", "monster_type": "storm", "weight": 9},
        {"name": "Хранитель лепестков", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 4},
        {"name": "Цветочная ведьма", "rarity": "legendary", "mood": "fear", "monster_type": "void", "weight": 3},
    ],
    "events": [
        {"type": "anomaly", "text": "Цветы поворачиваются к тебе одновременно, как будто слушают твои мысли.", "weight": 12},
        {"type": "trail", "text": "Пыльца складывается в стрелку и ведёт в глубину долины.", "weight": 9},
        {"type": "rift", "text": "Среди цветов мерцает тонкая щель иного мира.", "weight": 6},
    ],
},
"old_mine": {
    "monsters": [
        {"name": "Шахтный копун", "rarity": "common", "mood": "instinct", "monster_type": "bone", "weight": 23},
        {"name": "Кремневый жук", "rarity": "common", "mood": "instinct", "monster_type": "nature", "weight": 18},
        {"name": "Рудный скат", "rarity": "rare", "mood": "instinct", "monster_type": "bone", "weight": 15},
        {"name": "Кристальный сверчок", "rarity": "rare", "mood": "inspiration", "monster_type": "storm", "weight": 12},
        {"name": "Пыльный дозорный", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 10},
        {"name": "Глубинный ломатель", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 9},
        {"name": "Хранитель жилы", "rarity": "legendary", "mood": "instinct", "monster_type": "bone", "weight": 7},
        {"name": "Голос карьера", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 6},
    ],
    "events": [
        {"type": "cache", "text": "Ты находишь старый ящик шахтёров. Внутри ещё остались полезные вещи.", "weight": 10},
        {"type": "anomaly", "text": "Стены шахты гудят, как будто внутри камня что-то дышит.", "weight": 12},
        {"type": "trail", "text": "Крошки руды тянутся по полу, будто их кто-то уносил совсем недавно.", "weight": 8},
    ],
},
"rock_pass": {
    "monsters": [
        {"name": "Перевальный хрипун", "rarity": "common", "mood": "instinct", "monster_type": "shadow", "weight": 22},
        {"name": "Скальный грызень", "rarity": "common", "mood": "instinct", "monster_type": "bone", "weight": 18},
        {"name": "Буревой вьюн", "rarity": "rare", "mood": "rage", "monster_type": "storm", "weight": 16},
        {"name": "Каменный глашатай", "rarity": "rare", "mood": "inspiration", "monster_type": "echo", "weight": 12},
        {"name": "Седой страж перевала", "rarity": "epic", "mood": "instinct", "monster_type": "bone", "weight": 11},
        {"name": "Гранитный волк", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 9},
        {"name": "Небесный раскол", "rarity": "legendary", "mood": "rage", "monster_type": "storm", "weight": 7},
        {"name": "Горный пророк", "rarity": "legendary", "mood": "inspiration", "monster_type": "spirit", "weight": 5},
    ],
    "events": [
        {"type": "anomaly", "text": "Между камней проскальзывает искра и гаснет, оставляя запах грозы.", "weight": 12},
        {"type": "trail", "text": "На камне свежие царапины. Кто-то большой недавно прошёл через перевал.", "weight": 9},
        {"type": "cache", "text": "Под выступом спрятан походный схрон старых добытчиков.", "weight": 7},
    ],
},
"fog_pool": {
    "monsters": [
        {"name": "Туманный угорь", "rarity": "common", "mood": "fear", "monster_type": "shadow", "weight": 23},
        {"name": "Болотный дублёр", "rarity": "rare", "mood": "fear", "monster_type": "void", "weight": 17},
        {"name": "Вязкий сторож", "rarity": "rare", "mood": "instinct", "monster_type": "nature", "weight": 15},
        {"name": "Слизень омутов", "rarity": "common", "mood": "fear", "monster_type": "shadow", "weight": 20},
        {"name": "Чёрный камышовик", "rarity": "epic", "mood": "fear", "monster_type": "spirit", "weight": 10},
        {"name": "Глотатель следов", "rarity": "epic", "mood": "instinct", "monster_type": "bone", "weight": 8},
        {"name": "Хозяин тумана", "rarity": "legendary", "mood": "fear", "monster_type": "void", "weight": 4},
        {"name": "Омутная сирена", "rarity": "legendary", "mood": "inspiration", "monster_type": "echo", "weight": 3},
    ],
    "events": [
        {"type": "anomaly", "text": "Туман сгущается в силуэт и на миг идёт рядом с тобой.", "weight": 12},
        {"type": "rift", "text": "Поверхность воды дрожит, открывая мутную трещину в пространстве.", "weight": 6},
        {"type": "trail", "text": "Из грязи торчит амулет. Рядом следы тяжёлого существа.", "weight": 9},
    ],
},
"sunken_ruins": {
    "monsters": [
        {"name": "Руинный сторож", "rarity": "common", "mood": "fear", "monster_type": "bone", "weight": 20},
        {"name": "Утопший глаз", "rarity": "rare", "mood": "fear", "monster_type": "echo", "weight": 18},
        {"name": "Зов руин", "rarity": "rare", "mood": "inspiration", "monster_type": "spirit", "weight": 14},
        {"name": "Плесневый рыцарь", "rarity": "epic", "mood": "instinct", "monster_type": "bone", "weight": 12},
        {"name": "Смоляной дозор", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 10},
        {"name": "Архивариус бездны", "rarity": "legendary", "mood": "inspiration", "monster_type": "void", "weight": 7},
        {"name": "Утопший герольд", "rarity": "legendary", "mood": "fear", "monster_type": "echo", "weight": 6},
        {"name": "Маршевый колосс", "rarity": "legendary", "mood": "rage", "monster_type": "bone", "weight": 4},
    ],
    "events": [
        {"type": "cache", "text": "Ты находишь затопленный тайник древних жителей.", "weight": 10},
        {"type": "anomaly", "text": "Колонны руин отзываются гулом на твоё присутствие.", "weight": 12},
        {"type": "rift", "text": "В проломе между плитами мерцает иная глубина.", "weight": 7},
    ],
},
    "mushroom_path": {
        "monsters": [
            {"name": "Споровый слизень", "rarity": "common", "mood": "fear", "monster_type": "nature", "weight": 40},
            {"name": "Лесной глазун", "rarity": "common", "mood": "fear", "monster_type": "echo", "weight": 30},
            {"name": "Моховой шептун", "rarity": "rare", "mood": "inspiration", "monster_type": "nature", "weight": 15},
            {"name": "Грибной сторож", "rarity": "rare", "mood": "fear", "monster_type": "spirit", "weight": 10},
            {"name": "Сумеречный плодник", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 5},
        ],
        "events": [
            {"type": "anomaly", "text": "Ты замечаешь грибной круг. Воздух внутри него дрожит от страха.", "weight": 20},
            {"type": "trail", "text": "На земле видны следы маленьких лап. Кто-то наблюдает за тобой.", "weight": 15},
        ],
    },
    "wet_thicket": {
        "monsters": [
            {"name": "Корнехват", "rarity": "common", "mood": "fear", "monster_type": "nature", "weight": 35},
            {"name": "Тенелист", "rarity": "rare", "mood": "fear", "monster_type": "shadow", "weight": 25},
            {"name": "Сырой охотник", "rarity": "rare", "mood": "instinct", "monster_type": "nature", "weight": 20},
            {"name": "Влажный дух", "rarity": "epic", "mood": "inspiration", "monster_type": "spirit", "weight": 10},
            {"name": "Страж чащи", "rarity": "epic", "mood": "fear", "monster_type": "bone", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Чаща на миг сжимается вокруг тебя, будто реагирует на твои эмоции.", "weight": 18},
            {"type": "cache", "text": "Под корнями спрятано старое гнездо. Возможно, здесь кто-то линял.", "weight": 12},
        ],
    },
    "whisper_den": {
        "monsters": [
            {"name": "Шепчущий зрачок", "rarity": "rare", "mood": "fear", "monster_type": "echo", "weight": 30},
            {"name": "Корневой пророк", "rarity": "epic", "mood": "inspiration", "monster_type": "nature", "weight": 20},
            {"name": "Тревожный скользень", "rarity": "rare", "mood": "fear", "monster_type": "shadow", "weight": 25},
            {"name": "Безликий слухач", "rarity": "epic", "mood": "fear", "monster_type": "void", "weight": 15},
            {"name": "Сердце Шёпота", "rarity": "legendary", "mood": "fear", "monster_type": "echo", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Шёпот становится слишком понятным. Он произносит имя твоего активного монстра.", "weight": 24},
            {"type": "rift", "text": "Среди корней мерцает трещина. Кажется, эмоции здесь могут обрести форму.", "weight": 10},
        ],
    },
    "black_water": {
        "monsters": [
            {"name": "Зеркальный пиявец", "rarity": "common", "mood": "fear", "monster_type": "shadow", "weight": 35},
            {"name": "Илистый наблюдатель", "rarity": "rare", "mood": "fear", "monster_type": "spirit", "weight": 25},
            {"name": "Болотный двойник", "rarity": "epic", "mood": "fear", "monster_type": "shadow", "weight": 15},
            {"name": "Чёрный сомнамбул", "rarity": "rare", "mood": "inspiration", "monster_type": "void", "weight": 15},
            {"name": "Топкий хранитель", "rarity": "epic", "mood": "fear", "monster_type": "bone", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Вода показывает не твоё отражение, а неизвестного монстра.", "weight": 20},
            {"type": "echo", "text": "Ты слышишь плеск далеко в стороне. Возможно, это кто-то большой.", "weight": 14},
        ],
    },
    "fog_trail": {
        "monsters": [
            {"name": "Туманник", "rarity": "common", "mood": "fear", "monster_type": "shadow", "weight": 35},
            {"name": "Скользящий силуэт", "rarity": "rare", "mood": "fear", "monster_type": "storm", "weight": 25},
            {"name": "Слепой следопыт", "rarity": "rare", "mood": "instinct", "monster_type": "echo", "weight": 20},
            {"name": "Дымчатый оракул", "rarity": "epic", "mood": "inspiration", "monster_type": "spirit", "weight": 10},
            {"name": "Туманная пасть", "rarity": "epic", "mood": "fear", "monster_type": "void", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Туман уплотняется в фигуру и тут же распадается. Район резонирует со страхом.", "weight": 18},
            {"type": "trail", "text": "На грязи отпечатки когтей. Они внезапно обрываются.", "weight": 16},
        ],
    },
    "grave_of_voices": {
        "monsters": [
            {"name": "Курганный эхонид", "rarity": "rare", "mood": "fear", "monster_type": "bone", "weight": 30},
            {"name": "Погребальный мотылёк", "rarity": "rare", "mood": "inspiration", "monster_type": "spirit", "weight": 20},
            {"name": "Голос из ила", "rarity": "epic", "mood": "fear", "monster_type": "echo", "weight": 20},
            {"name": "Собиратель имён", "rarity": "epic", "mood": "fear", "monster_type": "void", "weight": 15},
            {"name": "Хор молчания", "rarity": "legendary", "mood": "fear", "monster_type": "spirit", "weight": 15},
        ],
        "events": [
            {"type": "anomaly", "text": "Голоса зовут тебя ближе. На миг кажется, что один из них принадлежит тебе.", "weight": 24},
            {"type": "altar", "text": "В иле торчит старый каменный знак. Такие места любят эмоциональные сущности.", "weight": 12},
        ],
    },
    "ash_slope": {
        "monsters": [
            {"name": "Пепельный ползун", "rarity": "common", "mood": "rage", "monster_type": "flame", "weight": 40},
            {"name": "Искровой шакал", "rarity": "rare", "mood": "rage", "monster_type": "flame", "weight": 25},
            {"name": "Шлакобой", "rarity": "rare", "mood": "instinct", "monster_type": "bone", "weight": 20},
            {"name": "Жаровой клык", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 10},
            {"name": "Магматический крикун", "rarity": "epic", "mood": "rage", "monster_type": "storm", "weight": 5},
        ],
        "events": [
            {"type": "anomaly", "text": "Пепел поднимается вихрем. Ярость локации словно ищет тело.", "weight": 18},
            {"type": "cache", "text": "Среди шлака виднеется осколок панциря. Похоже, кто-то пережил мутацию.", "weight": 12},
        ],
    },
    "lava_bridge": {
        "monsters": [
            {"name": "Лавовый гончий", "rarity": "rare", "mood": "rage", "monster_type": "flame", "weight": 30},
            {"name": "Кипящий сторож", "rarity": "rare", "mood": "rage", "monster_type": "storm", "weight": 25},
            {"name": "Огнехребет", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 20},
            {"name": "Мостовой ревун", "rarity": "epic", "mood": "instinct", "monster_type": "echo", "weight": 15},
            {"name": "Расплавленный каратель", "rarity": "legendary", "mood": "rage", "monster_type": "flame", "weight": 10},
        ],
        "events": [
            {"type": "anomaly", "text": "Лава под мостом вспыхивает ярче обычного. Кажется, она реагирует на любое колебание ярости.", "weight": 20},
            {"type": "boss_sign", "text": "На краю моста следы огромных когтей. Кто-то господствует здесь.", "weight": 14},
        ],
    },
    "heart_of_magma": {
        "monsters": [
            {"name": "Ядро пламени", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 25},
            {"name": "Магмовый берсерк", "rarity": "epic", "mood": "rage", "monster_type": "flame", "weight": 25},
            {"name": "Кровь кратера", "rarity": "legendary", "mood": "rage", "monster_type": "bone", "weight": 20},
            {"name": "Фениксовый осколок", "rarity": "legendary", "mood": "inspiration", "monster_type": "spirit", "weight": 15},
            {"name": "Сердце магмы", "rarity": "mythic", "mood": "rage", "monster_type": "storm", "weight": 15},
        ],
        "events": [
            {"type": "anomaly", "text": "Ядро вулкана пульсирует. Это место может усилить агрессивные мутации.", "weight": 24},
            {"type": "rift", "text": "В жарком мареве открывается разлом. В нём видно силуэт несуществующего монстра.", "weight": 12},
        ],
    },
}

RARITY_LABELS = {"common": "Обычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный", "mythic": "Мифический"}
MOOD_LABELS = {"rage": "🔥 Ярость", "fear": "😱 Страх", "instinct": "🎯 Инстинкт", "inspiration": "✨ Вдохновение"}

RARITY_STATS = {
    "common": {"hp": 20, "attack": 5, "capture": 0.72, "gold": 5, "exp": 4},
    "rare": {"hp": 30, "attack": 7, "capture": 0.52, "gold": 9, "exp": 6},
    "epic": {"hp": 42, "attack": 10, "capture": 0.30, "gold": 14, "exp": 8},
    "legendary": {"hp": 58, "attack": 13, "capture": 0.18, "gold": 20, "exp": 12},
    "mythic": {"hp": 80, "attack": 16, "capture": 0.10, "gold": 30, "exp": 18},
}

def _weighted_choice(items):
    total = sum(item["weight"] for item in items)
    roll = random.uniform(0, total)
    current = 0
    for item in items:
        current += item["weight"]
        if roll <= current:
            return item
    return items[-1]

def generate_district_encounter(district_slug: str):
    pool = DISTRICT_POOLS.get(district_slug)
    if not pool:
        return {"type": "empty", "text": "В этом районе пока нет настроенных встреч."}
    monster = _weighted_choice(pool["monsters"])
    event = _weighted_choice(pool["events"])
    if random.random() < 0.18:
        return {"type": "anomaly", "title": "⚠️ Эмоциональная аномалия", "text": event["text"], "hint": f"Эмоция района усиливается: {MOOD_LABELS.get(monster['mood'], monster['mood'])}"}
    if random.random() < 0.72:
        stats = RARITY_STATS[monster["rarity"]]
        return {
            "type": "monster",
            "title": "🐾 Встреча",
            "monster_name": monster["name"],
            "rarity": monster["rarity"],
            "rarity_label": RARITY_LABELS.get(monster["rarity"], monster["rarity"]),
            "mood": monster["mood"],
            "mood_label": MOOD_LABELS.get(monster["mood"], monster["mood"]),
            "monster_type": monster["monster_type"],
            "monster_type_label": TYPE_LABELS.get(monster["monster_type"], monster["monster_type"]),
            "hp": stats["hp"],
            "max_hp": stats["hp"],
            "attack": stats["attack"],
            "capture_chance": stats["capture"],
            "bonus_capture": 0.0,
            "counter_multiplier": 1.0,
            "reward_gold": stats["gold"],
            "reward_exp": stats["exp"],
            "text": f"Ты встречаешь существо: {monster['name']}",
        }
    return {"type": "event", "title": "✨ Событие района", "text": event["text"], "hint": "Здесь может скрываться особая эмоциональная реакция или редкая форма."}

def render_encounter_text(encounter: dict, attacker_type: str | None = None):
    if encounter["type"] == "monster":
        extra = ""
        if encounter.get("bonus_capture", 0) > 0:
            extra += f"\nБонус поимки: +{int(encounter['bonus_capture'] * 100)}%"
        type_hint = render_type_hint(attacker_type, encounter.get("monster_type"))
        return "\n".join([
            encounter["title"], "", encounter["text"],
            f"Редкость: {encounter['rarity_label']}",
            f"Эмоциональный след: {encounter['mood_label']}",
            f"Тип: {encounter.get('monster_type_label', '—')}",
            type_hint,
            f"HP: {encounter['hp']}/{encounter.get('max_hp', encounter['hp'])}",
            f"ATK: {encounter['attack']}{extra}", "",
            "Выбери действие: ⚔️ Атаковать / ✨ Навык / 🎯 Поймать / 🏃 Убежать",
        ])
    if encounter["type"] in {"anomaly", "event"}:
        lines = [encounter["title"], "", encounter["text"]]
        if encounter.get("hint"):
            lines.extend(["", encounter["hint"]])
        return "\n".join(lines)
    return encounter["text"]

def resolve_attack(encounter: dict, active_monster_attack: int = 10, attacker_type: str | None = None,
                   active_monster: dict | None = None):
    """
    Боевое разрешение атаки.
    - Применяет таблицу типов (рек. #3) — реально влияет на урон
    - Применяет комбо-бонусы к атаке (рек. #6)
    - Учитывает lifesteal из комбо-мутации
    """
    if encounter["type"] not in ("monster", "wildlife"):
        return {"ok": False, "text": "Здесь не на кого нападать."}
    # Нормализуем поля для зверей
    if encounter["type"] == "wildlife":
        if "monster_name" not in encounter:
            encounter["monster_name"] = encounter.get("name", "Зверь")
        if "monster_type" not in encounter:
            encounter["monster_type"] = "nature"

    # ── Тип-множитель (рек. #3) ──────────────────────────────────────────────
    multiplier = get_damage_multiplier(attacker_type, encounter.get("monster_type"))
    hint       = render_type_hint(attacker_type, encounter.get("monster_type"))

    # ── Комбо-бонус к атаке (рек. #6) ───────────────────────────────────────
    combo_atk_bonus = 0
    special_effect  = None
    if active_monster:
        from game.infection_service import get_combo_bonuses
        combo = get_combo_bonuses(active_monster)
        combo_atk_bonus = combo.get("atk_bonus", 0)
        special_effect  = combo.get("special")

    # ── Расчёт урона игрока ──────────────────────────────────────────────────
    base_dmg      = active_monster_attack + combo_atk_bonus
    player_attack = random.randint(max(4, base_dmg - 2), base_dmg + 3)
    player_attack = max(1, int(round(player_attack * multiplier)))

    encounter["hp"] -= player_attack

    # Lifesteal из комбо "Мрачный разрушитель"
    heal_amount = 0
    if special_effect == "lifesteal" and active_monster and player_attack > 0:
        heal_amount = max(1, player_attack // 4)
        active_monster["current_hp"] = min(
            active_monster.get("max_hp", 999),
            active_monster.get("current_hp", 0) + heal_amount
        )
        from database.repositories import save_monster
        save_monster(active_monster)

    # ── Победа ───────────────────────────────────────────────────────────────
    if encounter["hp"] <= 0:
        text = f"⚔️ Ты наносишь {player_attack} урона"
        if multiplier > 1.0:
            text += f" ({hint})"
        text += f" и побеждаешь {encounter['monster_name']}!"
        if heal_amount:
            text += f"\n🩸 Кража жизни: +{heal_amount} HP"
        return {
            "ok": True, "finished": True, "victory": True,
            "monster_defeated": True, "player_damage": 0,
            "text": text,
            "gold": encounter["reward_gold"], "exp": encounter["reward_exp"],
        }

    # ── Ответный удар врага ──────────────────────────────────────────────────
    # Комбо def_bonus снижает входящий урон
    combo_def_bonus = 0
    if active_monster:
        from game.infection_service import get_combo_bonuses
        combo = get_combo_bonuses(active_monster)
        combo_def_bonus = max(0, combo.get("def_bonus", 0))

    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    enemy_attack = max(0, int(enemy_attack * encounter.get("counter_multiplier", 1.0)))
    enemy_attack = max(0, enemy_attack - combo_def_bonus)
    encounter["counter_multiplier"] = 1.0

    text_parts = [f"⚔️ Ты наносишь {player_attack} урона."]
    if multiplier != 1.0:
        text_parts.append(hint)
    if heal_amount:
        text_parts.append(f"🩸 Кража жизни: +{heal_amount} HP")
    text_parts.append(
        f"{encounter['monster_name']} ещё держится. "
        f"HP: {max(0, encounter['hp'])}/{encounter.get('max_hp', encounter['hp'])}"
    )
    if enemy_attack > 0:
        text_parts.append(f"В ответ монстр атакует на {enemy_attack}.")
        if combo_def_bonus > 0:
            text_parts.append(f"🛡 Комбо-защита снижает урон на {combo_def_bonus}.")
    else:
        text_parts.append("Монстр не может пробить твою защиту!")

    return {
        "ok": True, "finished": False, "victory": False,
        "monster_defeated": False, "player_damage": enemy_attack,
        "text": "\n".join(text_parts),
    }

def resolve_capture(encounter: dict):
    if encounter["type"] not in ("monster", "wildlife"):
        return {"ok": False, "text": "Здесь нечего ловить."}
    base_hp = encounter.get("max_hp", encounter["hp"])
    bonus = 0.15 if encounter["hp"] <= max(1, base_hp // 2) else 0
    chance = min(0.95, encounter["capture_chance"] + bonus + encounter.get("bonus_capture", 0.0))
    success = random.random() <= chance
    if success:
        return {"ok": True, "finished": True, "captured": True, "player_damage": 0,
                "text": f"🎯 Ты успешно ловишь {encounter['monster_name']}!",
                "gold": encounter["reward_gold"] // 2, "exp": encounter["reward_exp"] + 1}
    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    enemy_attack = max(0, int(enemy_attack * encounter.get("counter_multiplier", 1.0)))
    encounter["counter_multiplier"] = 1.0
    return {"ok": True, "finished": False, "captured": False, "player_damage": enemy_attack,
            "text": f"🎯 Попытка поимки провалилась. {encounter['monster_name']} вырывается!\nВ ответ монстр атакует на {enemy_attack}."}

def calculate_flee_chance(player_level: int = 1, agility: int = 0,
                          enemy_level: int = 1, enemy_type: str = "monster",
                          has_flee_elixir: bool = False) -> float:
    """
    Рассчитывает шанс побега (0.10–0.90).
    Факторы: уровень героя, ловкость, уровень врага, тип врага, элексир побега.
    """
    base = 0.50
    base += player_level * 0.02        # +2% за уровень героя
    base += (agility // 5) * 0.05     # +5% за каждые 5 ловкости
    base -= enemy_level * 0.03        # -3% за уровень врага
    if enemy_type in ("world_boss", "boss"):
        base -= 0.25                  # штраф за боссов
    elif enemy_type == "elite":
        base -= 0.15                  # штраф за элитных

    if has_flee_elixir:
        base += 0.25                  # +25% от элексира
        base = max(0.40, base)        # минимум 40% с элексиром
    else:
        base = max(0.10, base)        # минимум 10% без элексира

    return min(0.90, base)


def resolve_flee(encounter: dict, player_level: int = 1, agility: int = 0,
                 has_flee_elixir: bool = False):
    """Попытка побега с учётом характеристик героя и врага."""
    if encounter["type"] not in ("monster", "wildlife"):
        return {"ok": True, "finished": True, "player_damage": 0,
                "text": "🏕 Ты возвращаешься в безопасную зону."}

    enemy_type = "monster"
    if encounter.get("type") == "world_boss":
        enemy_type = "world_boss"
    elif encounter.get("is_elite"):
        enemy_type = "elite"

    enemy_level = encounter.get("level", 1)
    chance = calculate_flee_chance(player_level, agility, enemy_level, enemy_type, has_flee_elixir)
    chance_pct = int(chance * 100)

    name = encounter.get("monster_name") or encounter.get("name", "существо")

    if random.random() <= chance:
        return {
            "ok": True, "finished": True, "player_damage": 0,
            "flee_success": True,
            "text": f"🏃 Тебе удалось сбежать от {name}!\n_(Шанс побега был {chance_pct}%)_",
        }

    # Неудача — враг контратакует
    enemy_attack = random.randint(max(2, encounter["attack"] - 2), encounter["attack"] + 2)
    enemy_attack = max(0, int(enemy_attack * encounter.get("counter_multiplier", 1.0)))
    encounter["counter_multiplier"] = 1.0
    return {
        "ok": True, "finished": False, "player_damage": enemy_attack,
        "flee_success": False,
        "text": f"❌ Побег не удался! {name} оказался быстрее...\n_(Шанс побега был {chance_pct}%)_",
    }


