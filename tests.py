import json


class TestError(Exception):
    pass


def questions_number(data):
    """ Хватает ли вопросов в каждой категории"""
    questions = data["questions"]
    categories = data["periods"]
    for category in categories:
        category_questions = list(
            filter(lambda question: question["period"] == category["name"],
                   data["questions"]))
        if len(category_questions) < category["length"]:
            raise TestError(f"В категории  {category['name']} нехватает "
                            f"вопросов: {len(category_questions)} вместо "
                            f"{category['length']}")
    return "Все категории имеют достаточно вопросов"


def questions_category(data):
    """Есть ли вопросы к несуществующим категориям"""
    categories = list(map(lambda category: category["name"],
                          data["periods"]))
    for question in data["questions"]:
        period = question["period"]
        if period not in categories:
            raise TestError(f"Вопрос {question['text'][:30]}... относится к"
                            f"несуществующей категории {period}")
    return "Все вопросы относятся к существующим категориям"


def is_period_jumps(data):
    """ Есть ли переходы между всеми периодами """
    categories = list(map(lambda category: category["name"],
                          data["periods"]))
    category_jumps = categories
    jumps = list(data["jumps"].keys())
    if category_jumps != jumps:
        raise TestError(f"Переходы различаются \n Нужны:   {category_jumps} \n "
                        f"Имеются: {jumps}")
    return "Имеются все необходимые переходы"


def is_null_question_variants(data):
    """ Есть ли вопросы без вариантов ответа """
    for question in data["questions"]:
        if len(question["answers"]) == 0:
            raise TestError(f"У вопроса {question['text'][:30]}... нет "
                            f"вариантов ответа")
    return "Все вопросы имеют варианты ответа"


def is_none_variant_causes(data):
    """  Есть ли вопросы без указания последствий """
    effects = ["government", "economy", "military", "territory",
               "prosperity"]
    for question in data['questions']:
        for answer in question["answers"]:
            if answer.get("effects", None) is None:
                raise TestError(
                    f"Ответ {answer['text'][:30]} вопроса "
                    f"{question['text'][:30]}"
                    f"Не имеет последствий")
            for effect in effects:
                if answer["effects"].get(effect) is None:
                    raise TestError(
                        f"Ответ {answer['text'][:30]} вопроса "
                        f"{question['text']}"
                        f"Не имеет поля {effect}")

    return "Все ответы имеют последствия"


def is_null_variant_causes(data):
    """ Есть ли вопросы с нулевыми последствиями """
    for question in data['questions']:
        for answer in question["answers"]:
            effects = answer["effects"].values()
            if all(list(map(lambda effect: effect == 0, effects))):
                raise TestError(
                    f"Ответ {answer['text'][:30]} вопроса "
                    f"{question['text'][:30]}... "
                    f"имеет нулевые последствия")
    return "Все ответы имеют ненулевые последствия"


def is_all_warnings(data):
    """Есть ли все предупреждения"""
    for stat in ["economy ", "military ", "government ", "territory ",
                 "prosperity "]:
        for status in ["low", "high"]:
            if stat + status not in data["warnings"]:
                raise TestError(f"Отсутствует предупреждение {stat + status}")
    if "time limit" not in data["warnings"]:
        raise TestError("Отсутствует предупреждение time limit")
    return "Все предупреждения на месте"


def is_all_endings(data):
    """Есть ли все концовки"""
    for stat in ["economy ", "military ", "government ", "territory ",
                 "prosperity "]:
        for status in ["min", "max"]:
            if stat + status not in data["endings"]:
                raise TestError(f"Отсутствует концовка {stat + status}")
    if "time limit" not in data["warnings"]:
        raise TestError("Отсутствует концовка time limit")
    return "Все концовки на месте"


def is_correct_start_values(data):
    """Корректны ли начальные значения игровых параметров"""
    for value in data["start_values"].items():
        if value[1] < data["value_min"] or value[1] > data["value_max"]:
            raise TestError(f"Значение {value[0]} некорректно (равно "
                            f"{value[1]}) и находится вне допустимых границ")
    return "Все начальные значения корректны"


def is_correct_periods_lengths(data):
    """Корректны ли длины каждого периода"""
    for period in data["periods"]:
        num = period["length"]
        if num < 1 or num > 8 or type(num) != int:
            raise TestError(f"Длина периода <{period['name']}> некорректна "
                            f"и равна {num}")
    return "Длины всех периодов корректны"


def all_quest_length(data):
    """Количество вопросов во всем квесте"""
    return f"Кол-во вопросов в квесте равно " \
        f"{sum(list(map(lambda x: x['length'], data['periods'])))}"


def longest_jump_text(data):
    """Размер самого длинного текста среди переходов"""
    long_jump = \
        sorted(list(map(lambda period: (period[0], period[1]['text']),
                        data['jumps'].items())), key=lambda x: len(x[1]))[-1]
    return f"Длина текста самого большого перехода равна {len(long_jump[1])}, "\
        f"он находится в периоде <{long_jump[0]}>"


def is_all_photos(data):
    """Проверяет наличие всех необходимых фото"""
    for name, image in list(map(lambda period: (period[0],
                                                period[1].get("image", None)),
                                data["jumps"].items())):
        if not image:
            raise TestError(f"Отсутствует изображение в периоде <{name}>")
    return "Все изображения на месте"


def analyse_records(records):
    """Анализ файла рекордов"""
    endings = {}
    for record in records.items():
        ending = record[1][0]
        name = record[0]
        number = record[1][1]
        endings[ending] = endings.get(ending, []) + [[name, number]]
    result = "Анализ рекордов: \n"
    for ending in endings.items():
        users = list(sorted(ending[1], key=lambda user: user[1]))
        users = list(map(lambda user: f"{user[0]} {str(user[1])}", users))
        users = "\n".join(users)
        result += f"С концовкой {ending[0]} игру прошли {len(ending[1])} " \
            f"игроков:\n{users} \n"
    return result


if __name__ == '__main__':
    with open("quest.json", "r", encoding="utf8") as file:
        quest = json.loads(file.read())
    # with open("records.json", "r", encoding="utf8") as file:
    #     records = json.loads(file.read())
    try:
        print(questions_number(quest))
        print(questions_category(quest))
        print(is_period_jumps(quest))
        print(is_null_question_variants(quest))
        print(is_none_variant_causes(quest))
        print(is_null_variant_causes(quest))
        print(is_all_warnings(quest))
        print(is_all_endings(quest))
        print(is_correct_start_values(quest))
        print(is_correct_periods_lengths(quest))
        print(is_all_photos(quest))
        print(all_quest_length(quest))
        print(longest_jump_text(quest))
        print(is_all_photos(quest))
        print("Все тесты пройдены успешно")
        # print(analyse_records(records))
    except TestError as error:
        print(error)
