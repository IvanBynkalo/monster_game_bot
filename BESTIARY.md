# 📖 БЕСТИАРИЙ — База данных монстров

> Документ для разработки. Пополняй вручную → передавай на реализацию в коде.
> Структура: Имя | Редкость | Тип | Эмоция | Как получить | Файл картинки | Статус

---

## Легенда

**Редкость:** common → rare → epic → legendary → mythic
**Типы:** nature / shadow / flame / bone / storm / echo / spirit / void
**Эмоции:** rage / fear / instinct / inspiration / sadness / joy / disgust / surprise
**Статус картинки:** ✅ есть | ❌ нет | 🔄 нужна новая

---

## 🗺 ИСТОЧНИК 1 — Встречи при исследовании

> Монстры появляются при исследовании районов. Можно поймать в бою.

### Тёмный лес — Тропа грибов (mushroom_path)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Споровый слизень | common | nature | fear | monster_nature.png | ❌ |
| Лесной глазун | common | echo | fear | monster_echo.png | ❌ |
| Моховой шептун | rare | nature | inspiration | monster_nature.png | ❌ |
| Грибной сторож | rare | spirit | fear | monster_spirit.png | ❌ |
| Сумеречный плодник | epic | shadow | fear | monster_shadow.png | ❌ |

### Тёмный лес — Сырая чаща (wet_thicket)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Корнехват | common | nature | fear | monster_nature.png | ❌ |
| Тенелист | rare | shadow | fear | monster_shadow.png | ❌ |
| Сырой охотник | rare | nature | instinct | monster_nature.png | ❌ |
| Влажный дух | epic | spirit | inspiration | monster_spirit.png | ❌ |
| Страж чащи | epic | bone | fear | monster_bone.png | ❌ |

### Тёмный лес — Логово шепчущих (whisper_den)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Шепчущий зрачок | rare | echo | fear | monster_echo.png | ❌ |
| Корневой пророк | epic | nature | inspiration | monster_nature.png | ❌ |
| Тревожный скользень | rare | shadow | fear | monster_shadow.png | ❌ |
| Безликий слухач | epic | void | fear | monster_void.png | ❌ |
| Сердце Шёпота | legendary | echo | fear | monster_echo.png | ❌ |

### Изумрудные поля — Зелёный луг (green_meadow)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Луговой прыгун | common | nature | inspiration | monster_nature.png | ❌ |
| Светлый мотылёк | common | echo | inspiration | monster_echo.png | ❌ |
| Травяной сторож | rare | nature | instinct | monster_nature.png | ❌ |
| Росный пастух | rare | spirit | inspiration | monster_spirit.png | ❌ |
| Жемчужный кузнечик | rare | storm | instinct | monster_storm.png | ❌ |
| Эхо-перепел | epic | echo | inspiration | monster_echo.png | ❌ |
| Страж лугов | epic | bone | instinct | monster_bone.png | ❌ |
| Солнечный хищник | legendary | flame | rage | monster_flame.png | ❌ |

### Изумрудные поля — Цветочная долина (flower_valley)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Пыльцевой дух | common | spirit | inspiration | monster_spirit.png | ❌ |
| Лепестковый лис | rare | nature | inspiration | monster_nature.png | ❌ |
| Медовый шёпот | rare | echo | inspiration | monster_echo.png | ❌ |
| Садовый страж | rare | nature | instinct | monster_nature.png | ❌ |
| Полевой змеец | epic | shadow | fear | monster_shadow.png | ❌ |
| Венец рассвета | epic | storm | inspiration | monster_storm.png | ❌ |
| Хранитель лепестков | legendary | echo | inspiration | monster_echo.png | ❌ |
| Цветочная ведьма | legendary | void | fear | monster_void.png | ❌ |

### Каменные холмы — Старая шахта (old_mine)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Шахтный копун | common | bone | instinct | monster_bone.png | ❌ |
| Кремневый жук | common | nature | instinct | monster_nature.png | ❌ |
| Рудный скат | rare | bone | instinct | monster_bone.png | ❌ |
| Кристальный сверчок | rare | storm | inspiration | monster_storm.png | ❌ |
| Пыльный дозорный | epic | shadow | fear | monster_shadow.png | ❌ |
| Глубинный ломатель | epic | flame | rage | monster_flame.png | ❌ |
| Хранитель жилы | legendary | bone | instinct | monster_bone.png | ❌ |
| Голос карьера | legendary | echo | inspiration | monster_echo.png | ❌ |

### Каменные холмы — Каменный перевал (rock_pass)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Перевальный хрипун | common | shadow | instinct | monster_shadow.png | ❌ |
| Скальный грызень | common | bone | instinct | monster_bone.png | ❌ |
| Буревой вьюн | rare | storm | rage | monster_storm.png | ❌ |
| Каменный глашатай | rare | echo | inspiration | monster_echo.png | ❌ |
| Седой страж перевала | epic | bone | instinct | monster_bone.png | ❌ |
| Гранитный волк | epic | flame | rage | monster_flame.png | ❌ |
| Небесный раскол | legendary | storm | rage | monster_storm.png | ❌ |
| Горный пророк | legendary | spirit | inspiration | monster_spirit.png | ❌ |

### Болота теней — Туманный омут (fog_pool)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Туманный угорь | common | shadow | fear | monster_shadow.png | ❌ |
| Болотный дублёр | rare | void | fear | monster_void.png | ❌ |
| Вязкий сторож | rare | nature | instinct | monster_nature.png | ❌ |
| Чёрный камышовик | epic | spirit | fear | monster_spirit.png | ❌ |
| Глотатель следов | epic | bone | instinct | monster_bone.png | ❌ |
| Хозяин тумана | legendary | void | fear | monster_void.png | ❌ |
| Омутная сирена | legendary | echo | inspiration | monster_echo.png | ❌ |

### Болота теней — Утопшие руины (sunken_ruins)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Руинный сторож | common | bone | fear | monster_bone.png | ❌ |
| Утопший глаз | rare | echo | fear | monster_echo.png | ❌ |
| Зов руин | rare | spirit | inspiration | monster_spirit.png | ❌ |
| Плесневый рыцарь | epic | bone | instinct | monster_bone.png | ❌ |
| Смоляной дозор | epic | shadow | fear | monster_shadow.png | ❌ |
| Архивариус бездны | legendary | void | inspiration | monster_void.png | ❌ |
| Утопший герольд | legendary | echo | fear | monster_echo.png | ❌ |
| Маршевый колосс | legendary | bone | rage | monster_bone.png | ❌ |

### Болото теней — Чёрная вода (black_water)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Зеркальный пиявец | common | shadow | fear | monster_shadow.png | ❌ |
| Слизень омутов | common | shadow | fear | monster_shadow.png | ❌ |
| Илистый наблюдатель | rare | spirit | fear | monster_spirit.png | ❌ |
| Болотный двойник | epic | shadow | fear | monster_shadow.png | ❌ |
| Чёрный сомнамбул | rare | void | inspiration | monster_void.png | ❌ |
| Топкий хранитель | epic | bone | fear | monster_bone.png | ❌ |

### Болото теней — Туманная тропа (fog_trail)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Туманник | common | shadow | fear | monster_shadow.png | ❌ |
| Скользящий силуэт | rare | storm | fear | monster_storm.png | ❌ |
| Слепой следопыт | rare | echo | instinct | monster_echo.png | ❌ |
| Дымчатый оракул | epic | spirit | inspiration | monster_spirit.png | ❌ |
| Туманная пасть | epic | void | fear | monster_void.png | ❌ |

### Болото теней — Кладбище голосов (grave_of_voices)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Курганный эхонид | rare | bone | fear | monster_bone.png | ❌ |
| Погребальный мотылёк | rare | spirit | inspiration | monster_spirit.png | ❌ |
| Голос из ила | epic | echo | fear | monster_echo.png | ❌ |
| Собиратель имён | epic | void | fear | monster_void.png | ❌ |
| Хор молчания | legendary | spirit | fear | monster_spirit.png | ❌ |

### Вулкан ярости — Пепельный склон (ash_slope)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Пепельный ползун | common | flame | rage | monster_flame.png | ❌ |
| Искровой шакал | rare | flame | rage | monster_flame.png | ❌ |
| Шлакобой | rare | bone | instinct | monster_bone.png | ❌ |
| Жаровой клык | epic | flame | rage | monster_flame.png | ❌ |
| Магматический крикун | epic | storm | rage | monster_storm.png | ❌ |

### Вулкан ярости — Лавовый мост (lava_bridge)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Лавовый гончий | rare | flame | rage | monster_flame.png | ❌ |
| Кипящий сторож | rare | storm | rage | monster_storm.png | ❌ |
| Огнехребет | epic | flame | rage | monster_flame.png | ❌ |
| Мостовой ревун | epic | echo | instinct | monster_echo.png | ❌ |
| Расплавленный каратель | legendary | flame | rage | monster_flame.png | ❌ |

### Вулкан ярости — Сердце магмы (heart_of_magma)
| Имя | Редкость | Тип | Эмоция | Файл картинки | Статус |
|---|---|---|---|---|---|
| Ядро пламени | epic | flame | rage | monster_flame.png | ❌ |
| Магмовый берсерк | epic | flame | rage | monster_flame.png | ❌ |
| Кровь кратера | legendary | bone | rage | monster_bone.png | ❌ |
| Фениксовый осколок | legendary | spirit | inspiration | monster_spirit.png | ❌ |
| Сердце магмы | **mythic** | storm | rage | monster_mythic_flame.png | ❌ |

### Элитные зоны (спец. экспедиция)
| Имя | Зона | Редкость | Тип | Файл картинки | Статус |
|---|---|---|---|---|---|
| Чащобный альфа | elite_forest | epic | nature | monster_nature.png | ❌ |
| Шёпот кроны | elite_forest | epic | echo | monster_echo.png | ❌ |
| Корнепасть | elite_forest | legendary | nature | monster_nature.png | ❌ |
| Хранитель старого дуба | elite_forest | legendary | bone | monster_bone.png | ❌ |
| Хребтовый колун | elite_hills | epic | bone | monster_bone.png | ❌ |
| Синий разрушитель | elite_hills | epic | storm | monster_storm.png | ❌ |
| Старший монолит | elite_hills | legendary | bone | monster_bone.png | ❌ |
| Глас разлома | elite_hills | legendary | echo | monster_echo.png | ❌ |
| Топный ловчий | elite_marsh | epic | shadow | monster_shadow.png | ❌ |
| Смоляной жрец | elite_marsh | epic | void | monster_void.png | ❌ |
| Болотный владыка | elite_marsh | legendary | shadow | monster_shadow.png | ❌ |
| Омутный архив | elite_marsh | legendary | echo | monster_echo.png | ❌ |

---

## 🏪 ИСТОЧНИК 2 — Магазин Варга (купить за золото)

| Имя | Редкость | Тип | Эмоция | Цена | Файл картинки | Статус |
|---|---|---|---|---|---|---|
| Лесной спрайт | rare | nature | inspiration | 90з | monster_nature.png | ❌ |
| Болотный охотник | rare | shadow | instinct | 105з | monster_shadow.png | ❌ |
| Угольный клык | epic | flame | rage | 160з | monster_flame.png | ❌ |

> Добавить монстра: game/shop_service.py → MONSTER_SHOP_OFFERS

---

## 🕳 ИСТОЧНИК 3 — Подземелья (бой, поимка невозможна)

### Рядовые враги
| Имя | Тема подземелья | Файл картинки | Статус |
|---|---|---|---|
| Корневой хищник | forest | monster_nature.png | ❌ |
| Чащобный зверь | forest | monster_nature.png | ❌ |
| Каменный бур | stone | monster_bone.png | ❌ |
| Пещерный ломатель | stone | monster_bone.png | ❌ |
| Болотный пастух | marsh | monster_shadow.png | ❌ |
| Смоляной охотник | marsh | monster_shadow.png | ❌ |

### Боссы подземелий (финальная комната)
| Имя | Подземелье | HP | Файл картинки | Статус |
|---|---|---|---|---|
| Хозяин корней | dark_forest | 60 | monster_boss_forest.png | ❌ |
| Сердце монолита | stone_hills | 66 | monster_boss_stone.png | ❌ |
| Тёмный омутник | shadow_marsh | 64 | monster_boss_marsh.png | ❌ |

---

## 👑 ИСТОЧНИК 4 — Мировые боссы (появляются при 85%+ исследования)

| Имя | Локация | HP | Тип | Файл картинки | Статус |
|---|---|---|---|---|---|
| Древний страж леса | dark_forest | 120 | nature | monster_world_forest.png | ❌ |
| Колосс камня | stone_hills | 145 | bone | monster_world_stone.png | ❌ |
| Повелитель болот | shadow_marsh | 130 | shadow | monster_world_marsh.png | ❌ |

---

## ✨ ИСТОЧНИК 5 — Эмоциональное рождение

> Накопить эмоции → ритуал в особом месте. Имя генерируется из пула слов.

| Эмоция | Порог | Тип | Примеры имён | Файл картинки | Статус |
|---|---|---|---|---|---|
| rage | 40 | flame | Пламенный Разрушитель, Алый Берсерк | birth_rage.png | ❌ |
| fear | 40 | shadow | Теневой Наблюдатель, Бледный Призрак | birth_fear.png | ❌ |
| instinct | 40 | nature | Первозданный Охотник, Дикий Вожак | birth_instinct.png | ❌ |
| inspiration | 40 | spirit | Небесный Вестник, Сияющий Хранитель | birth_inspiration.png | ❌ |
| sadness | 50 | void | Угасший Странник, Туманный Молчун | birth_sadness.png | ❌ |
| joy | 35 | echo | Золотой Плясун, Искристый Озорник | birth_joy.png | ❌ |
| disgust | 45 | shadow | Ядовитый Осквернитель, Гнилостный Токсин | birth_disgust.png | ❌ |
| surprise | 30 | storm | Хаотичный Феномен, Внезапный Парадокс | birth_surprise.png | ❌ |

---

## 🥚 ИСТОЧНИК 6 — Яйца (код частичный, не реализовано полностью)

| Тип яйца | Где находится | Время вылупления | Что вылупляется | Файл | Статус |
|---|---|---|---|---|---|
| Лесное яйцо | dark_forest | ? ч | ? | egg_nature.png | ❌ |
| Болотное яйцо | shadow_marsh / shadow_swamp | ? ч | ? | egg_shadow.png | ❌ |
| Огненное яйцо | volcano_wrath | ? ч | ? | egg_flame.png | ❌ |
| Каменное яйцо | stone_hills | ? ч | ? | egg_bone.png | ❌ |
| Небесное яйцо | emerald_fields | ? ч | ? | egg_spirit.png | ❌ |

> ⬆️ Заполни: время вылупления и какой монстр вылупляется

---

## 🏆 ИСТОЧНИК 7 — Трофейная поимка боссов (не реализовано)

| Трофей | Из босса | Шанс | Тип | Файл | Статус |
|---|---|---|---|---|---|
| Отросток корней | Хозяин корней | 15% | nature | monster_trophy_forest.png | ❌ |
| Кристальный осколок | Сердце монолита | 12% | bone | monster_trophy_stone.png | ❌ |
| Тень омута | Тёмный омутник | 10% | shadow | monster_trophy_marsh.png | ❌ |
| Искра стража | Древний страж леса | 5% | nature | monster_trophy_world_forest.png | ❌ |
| Осколок колосса | Колосс камня | 5% | bone | monster_trophy_world_stone.png | ❌ |
| Болотный дух | Повелитель болот | 5% | shadow | monster_trophy_world_marsh.png | ❌ |

---

## 📊 Статистика

| Источник | Монстров | Статус кода |
|---|---|---|
| Встречи в районах | 115 | ✅ готово |
| Магазин Варга | 3 | ✅ готово |
| Подземелья рядовые | 6 | ✅ готово |
| Боссы подземелий | 3 | ✅ готово (не поимаются) |
| Мировые боссы | 3 | ✅ готово (не поимаются) |
| Эмоц. рождение | ∞ генерация | ✅ готово |
| Яйца | 5 видов | 🔄 частично |
| Трофеи боссов | 6 | ❌ не реализовано |
| **Итого уникальных имён** | **~130+** | |

---

## 🖼 Все нужные картинки

### Типовые (8 штук — по типу монстра)
| Файл | Тип | Статус |
|---|---|---|
| monster_nature.png | nature | ❌ |
| monster_shadow.png | shadow | ❌ |
| monster_flame.png | flame | ❌ |
| monster_bone.png | bone | ❌ |
| monster_storm.png | storm | ❌ |
| monster_echo.png | echo | ❌ |
| monster_spirit.png | spirit | ❌ |
| monster_void.png | void | ❌ |

### Боссы подземелий (3 штуки)
| Файл | Статус |
|---|---|
| monster_boss_forest.png | ❌ |
| monster_boss_stone.png | ❌ |
| monster_boss_marsh.png | ❌ |

### Мировые боссы (3 штуки)
| Файл | Статус |
|---|---|
| monster_world_forest.png | ❌ |
| monster_world_stone.png | ❌ |
| monster_world_marsh.png | ❌ |

### Эмоциональное рождение (8 штук)
| Файл | Статус |
|---|---|
| birth_rage.png | ❌ |
| birth_fear.png | ❌ |
| birth_instinct.png | ❌ |
| birth_inspiration.png | ❌ |
| birth_sadness.png | ❌ |
| birth_joy.png | ❌ |
| birth_disgust.png | ❌ |
| birth_surprise.png | ❌ |

### Яйца (5 штук)
| Файл | Статус |
|---|---|
| egg_nature.png | ❌ |
| egg_shadow.png | ❌ |
| egg_flame.png | ❌ |
| egg_bone.png | ❌ |
| egg_spirit.png | ❌ |

### Трофеи боссов (6 штук)
| Файл | Статус |
|---|---|
| monster_trophy_forest.png | ❌ |
| monster_trophy_stone.png | ❌ |
| monster_trophy_marsh.png | ❌ |
| monster_trophy_world_forest.png | ❌ |
| monster_trophy_world_stone.png | ❌ |
| monster_trophy_world_marsh.png | ❌ |

### Мифические (1 штука)
| Файл | Статус |
|---|---|
| monster_mythic_flame.png | ❌ |

**Итого картинок нужно: 34**

---

## 📝 Как пополнять

**Добавить монстра во встречи:**
Укажи: имя | редкость | тип | эмоция | район — добавлю в encounter_service.py

**Добавить в магазин:**
Укажи: имя | редкость | тип | эмоция | цена | HP | атака — добавлю в shop_service.py

**Заполнить яйца:**
Укажи: тип яйца | время вылупления (часы) | что вылупляется

**Добавить трофей босса:**
Укажи: имя трофея | из какого босса | шанс % | HP | атака
