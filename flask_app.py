from flask import Flask, request
import logging
import random
import json

site = "PenzaStreetNetworks"


class User:
    """Пользователь навыка"""
    quest_data = {}

    def __init__(self, id):
        self.set_base(id)

    def set_base(self, id):
        self.move = 0
        self.id = id
        self.period = ""
        self.government = quest["start_values"]["government"]
        self.economy = quest["start_values"]["economy"]
        self.military = quest["start_values"]["military"]
        self.control = quest["start_values"]["control"]
        self.communism = quest["start_values"]["communism"]
        self.questions = []
        self.jumps_questions = []
        self.fail = "questions limit"

    def get_params(self):
        """Возвращает параметры страны"""
        return {
            "government": self.government,
            "economy": self.economy,
            "military": self.military,
            "control": self.control,
            "communism": self.communism,
        }

    def change_params(self, params):
        """Изменяет параметры страны"""
        self.government += params["government"]
        self.economy += params["economy"]
        self.military += params["military"]
        self.control += params["control"]
        self.communism += params["communism"]
        step = 0.35
        delta = params.copy()
        delta["communism"] = (sum([self.government, self.economy,
                                    self.military, self.control])
                              / 4 - 50) * step
        self.communism += delta["communism"]
        return delta

    def print_state(self):
        name = sessionStorage[self.id]["first_name"]
        current = sessionStorage[self.id]["current_question"]
        state = f"{round(self.government, 2)}, {round(self.economy, 2)}, " \
            f"{round(self.military, 2)}, " \
            f"{round(self.control, 2)}, ({round(self.communism, 2)})"
        return f"{name}: {state} [{current}]"

    def __str__(self):
        """Возвращает параметры страны в виде строки"""
        return f"Политическая мощь: {round(self.government, 2)}\n" + \
               f"Экономика: {round(self.economy, 2)}\n" + \
               f"Военная мощь: {round(self.military, 2)}\n" + \
               f"Котроль над народом: {round(self.control, 2)}\n" + \
               f"Коммунизм: {round(self.communism, 2)}\n"


class Question:
    """Вопрос игры"""

    def __init__(self, obj):
        """инициализация вопроса"""
        self.text = obj["text"]
        self.reference = obj["reference"]
        self.date = obj["date"]
        self.period = obj["period"]
        self.answers = obj["answers"]

    def get_answers_titles(self):
        """Вывод текста вариантов ответа"""
        return [el["text"] for el in self.answers]

    def get_effects_on_answer(self, data):
        """Последствия ответа"""
        k = quest["k"]
        for answer in self.answers:
            if transform_answer(answer["text"]) == data:
                for effect in answer["effects"]:
                    answer["effects"][effect] *= k
                return answer["effects"]

    def get_real_answer(self):
        for el in self.answers:
            if not el["alternative"]:
                return el["text"]
        return False

    def get_cause_effect(self, data):
        """Вывод текста последствий"""
        for answer in self.answers:
            if transform_answer(answer["text"]) == data:
                return answer["cause"]

    def __str__(self):
        """Возвращает текст вопроса"""
        return self.text


def transform_answer(string):
    """Подгонка ответа пользователя под один формат"""
    return string.strip(".").lower().capitalize()


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
sessionStorage = {}
with open(f"/home/{site}/mysite/quest.json", "r",
          encoding="utf8") as file:
    quest = json.loads(file.read())
hint_button_text = "Подсказка"



@app.route('/red_dream', methods=['POST'])
def main():
    """Каркас диалога с пользователем и Алисой"""
    # logging.info('Request: %r', request.json)

    User.quest_data = quest

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    user_id = request.json['session']['user_id']

    start(request.json, response)

    # logging.info('Response: %r', request.json)

    return json.dumps(response)


def start(req, res):
    """Начало разговора с пользователем"""
    user_id = req['session']['user_id']

    answer = transform_answer(req["request"]["original_utterance"])

    if answer == "Помощь":
        res['response']['text'] = quest["help"]
        init_buttons(req, res)
        return

    if answer == "Что ты умеешь":
        res['response']['text'] = "Я умею играть с тобой в Красную Мечту. "\
                                  "В ней я задаю тебе исторические вопросы, "\
                                  "а ты выбираешь варианты ответов, как " \
                                  "настоящий правитель страны. Если тебе " \
                                  "будет сложно, то я могу подсказать, как" \
                                  "всё было на самом деле."
        init_buttons(req, res)
        return

    if answer == "Создатели":
        res['response']['text'] = quest["credits"]
        return

    if req['session']['new']:
        res['response']['text'] = 'Привет! Вы включили навык-игру ' \
                                  '"Красная мечта". ' \
                                  'Я буду задавать вопросы по управлению ' \
                                  'страной, а ты будешь выбирать ответ ' \
                                  'из предложенных вариантов. Можешь сказать ' \
                                  '\"подсказка\" и я тебе могу сказать ' \
                                  'решение исторического лидера. ' \
                                  'Назови своё имя!'
        user = User(user_id)
        user.questions, user.jumps_questions = make_questions_list(
            User.quest_data)
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,
            'user': user,
            "current_question": 0,
            "echo_effect": False,
            "buttons": [],
        }
        res['response']['buttons'] = [
            {
                "title": "Помощь",
                "hide": False
            },
            {
                "title": "Что ты умеешь",
                "hide": False
            }
        ]
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['game_started'] = True
            handle_dialog(req, res)

    else:

        handle_dialog(req, res)


def handle_dialog(req, res):
    """Обработка диалога"""
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]["user"]
    logging.info(user.print_state())
    answer = transform_answer(req["request"]["original_utterance"])
    if sessionStorage[user_id].get('end_quest') == True:
        return end(req, res)

    if answer in ["Статистика", "статистика"]:
        current = sessionStorage[user_id]['current_question'] - 1
        question = Question(user.questions[current])
        res['response']['text'] = str(user) + f"\n {str(question)}"
        init_buttons(req, res)
        return
    if answer in ["Помощь", "помощь"]:
        res['response']['text'] = quest["help"]
        init_buttons(req, res)
        return
    elif answer in ["Рекорды", "рекорды"]:
        res['response']['text'] = get_records()
        return

    posible_answers = list(map(
        transform_answer, sessionStorage[user_id]["buttons"]))
    if posible_answers and not answer in posible_answers:
        res['response']['text'] = "Что? Я не расслышала."
        init_buttons(req, res)
        return
    try:
        if not is_liveable(req, res, user.get_params()):
            sessionStorage[user_id]['end_quest'] = True
            return end(req, res)

        current = sessionStorage[user_id]['current_question']

        echo_effect = sessionStorage[user_id]['echo_effect']
        next_question = Question(user.questions[current])

        if current and echo_effect and answer != "Завершить правление":
            past_question = Question(user.questions[current - 1])
            effect = past_question.get_cause_effect(answer)
            reference = past_question.reference

            if answer.lower() == hint_button_text.lower():
                if reference:
                    question = Question(user.questions[current])
                    res['response']['text'] = reference + \
                        f"\n***\n{str(past_question)}"
                    res["response"]["tts"] = f"{reference} {past_question}"
                else:
                    res["response"]["text"] = quest["alternative_hint"]
                init_buttons(req, res)
                return

            if answer not in ["Начать правление", "Завершить правление"]:
                analyze_answer(req, res, effect,
                               past_question.get_effects_on_answer(answer))
                res["response"]["tts"] = effect
            if current in list(user.jumps_questions):
                init_buttons(req, res, ["Завершить правление"])

                return
            if current in user.jumps_questions:
                res['response']['text'] = ""
            res['response']['text'] += f"\n***\n {str(next_question)}"
            res['response']['tts'] = res["response"].get("tts", "") + " " + str(
                next_question)

            init_buttons(req, res, next_question.get_answers_titles() + [
                hint_button_text, "Статистика"])
            sessionStorage[user_id]['current_question'] += 1
            # init_buttons(req, res, ["Дальше", "Статистика"])

            return
        if answer == "Завершить правление" or current in user.jumps_questions:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = user.jumps_questions[
                                                   current].title() + "." + quest["jumps"][
                                                   user.jumps_questions[current]]["text"]
            res['response']['card']['image_id'] = quest["jumps"][
                user.jumps_questions[current]]["image"]
            res['response']['text'] = user.jumps_questions[current].title()
            res["response"]["tts"] = res["response"].get("tts", "") + quest[
                "jumps"][user.jumps_questions[current]]["text"]

            init_buttons(req, res, ["Начать правление"])
            del user.jumps_questions[current]
            return
        res['response']['text'] = str(next_question)

        init_buttons(req, res, next_question.get_answers_titles() + [hint_button_text, "Статистика"])
        sessionStorage[user_id]['current_question'] += 1
        sessionStorage[user_id]['echo_effect'] = True

        return
    except IndexError:
        sessionStorage[user_id]['end_quest'] = True
        res['response']['text'] = quest['endings']['time limit']
        init_buttons(req, res, ["Завершить"])
        return


def end(req, res):
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]["user"]
    answer = transform_answer(req["request"]["original_utterance"])
    with open(f"/home/{site}/mysite/records.json", "r",
              encoding="utf8") as file:
        past_records = dict(json.loads(file.read()))
    records = {sessionStorage[user_id]['first_name']: [
        user.fail, sessionStorage[user_id]["current_question"]]}
    records = dict(list(records.items()) + list(past_records.items()))
    with open(f"/home/{site}/mysite/records.json", "w",
              encoding="utf8") as file:
        file.write(json.dumps(records))
    if answer == "Создатели":
        res['response']['text'] = quest["credits"]
    elif answer == "Рекорды":
        res['response']['text'] = get_records()
    elif answer == "Сыграть еще раз":
        sessionStorage[user_id]['end_quest'] = False
        req['session']['new'] = True
        return start(req, res)
    elif answer == "Завершить":
        res["response"]["text"] = f"Спасибо, что поиграл со мной " \
            f"{sessionStorage[user_id]['first_name'].title()}! Пока."
        res["end_session"] = True
    else:
        res['response']['text'] = "Вы прошли квест."
    init_buttons(req, res, ["Сыграть еще раз", "Рекорды", "Создатели",
                            "Завершить"])
    return


def analyze_answer(req, res, effect, params):
    """Анализ ответа пользователя"""
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]['user']
    delta = user.change_params(params)
    res['response']['text'] = effect + string_effects(delta, delta=True)
    if not is_liveable(req, res, user.get_params()):
        res['response']['text'] += '\nИгра закончена!'

        return
    return


def get_first_name(req):
    """Получение имени пользователя"""
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


def change_period(req, res, count_answers, users_answers):
    """ Проверка смены периода """
    if count_answers == users_answers:
        res['response']['text'] = ""
        # Здесь переход в новую эпоху
    return


def is_liveable(req, res, params):
    """ Проверка жизнеспособности страны """
    user_id = req['session']['user_id']
    echo = res['response'].get('text', '')
    user = sessionStorage[user_id]["user"]

    for param in params:
        if params[param] >= quest["value_max"]:
            echo += "\n\n" + User.quest_data["endings"][f"{param} max"]
            res['response']["text"] = echo
            res["response"]["tts"] = res["response"].get("tts", "") + "\n" + echo
            user.fail = f"{param} max"
            return False
        elif params[param] <= quest["value_min"]:
            echo += "\n\n" + User.quest_data["endings"][f"{param} min"]
            res['response']["text"] = echo
            res["response"]["tts"] = res["response"].get("tts", "") + "\n" + echo
            user.fail = f"{param} min"
            return False
        elif params[param] >= quest["value_lot"]:
            echo += "\n\n" + User.quest_data["warnings"][f"{param} high"]
            res['response']["text"] = echo
            return True
        elif params[param] <= quest["value_few"]:
            echo += "\n\n" + User.quest_data["warnings"][f"{param} low"]
            res['response']["text"] = echo
            return True
    return True


def question(req, res, text, variants, results):
    """ Показ вопроса, вариантов ответа и вывод последствий. """
    # results - список ответов в том же порядке вопросов
    res['response']['text'] = text
    init_buttons(req, res, variants + [hint_button_text])
    answer = transform_answer(req["request"]["original_utterance"])
    for i, result in enumerate(variants):
        if answer == hint_button_text:
            res['response']['text'] = quest["hint"]
        elif answer == result:
            res['response']['text'] = results[i]


def init_buttons(req, res, buttons=None):
    """Инициализация кнопок"""
    if not sessionStorage:
        res['response']['buttons'] = [
            {
                "title": "Помощь",
                "hide": False
            },
            {
                "title": "Что ты умеешь",
                "hide": False
            }
        ]
        return
    user_id = req['session']['user_id']
    if not buttons:
        if not sessionStorage[user_id].get("buttons"):
            res['response']['buttons'] = [
                {
                    "title": "Помощь",
                    "hide": False
                },
                {
                    "title": "Что ты умеешь",
                    "hide": False
                }
            ]
            return
        buttons = sessionStorage[user_id]["buttons"].copy()
    res['response']['buttons'] = [
        {
            'title': button,
            'hide': True
        } for button in buttons

    ] + [
        {
            "title": "Помощь",
            "hide": False
        },
        {
            "title": "Что ты умеешь",
            "hide": False
        }
    ]
    sessionStorage[user_id]["buttons"] = buttons.copy()


def make_questions_list(data):
    """создание списка вопросов"""
    questions_list = []
    counts = {}
    for question in sorted(data["questions"], key=lambda key: random.random()):
        counts[question["period"]] = counts.get(question["period"], 0) + 1
        this_period = list(filter(lambda period: period["name"] == question[
            "period"], quest["periods"]))[0]
        if counts[question["period"]] <= this_period["length"]:
            questions_list.append(question)

    questions_list.sort(key=lambda el: el["date"])
    jumps_questions = {0: questions_list[0]["period"]}

    for item, question in enumerate(questions_list):
        if item and question["period"] != questions_list[item - 1]["period"]:
            jumps_questions[item] = question["period"]

    return questions_list, jumps_questions


def string_effects(effects, delta=False):
    """Вывод изменений в стране в читаемом виде"""
    government = round(effects["government"], 2)
    economy = round(effects["economy"], 2)
    military = round(effects["military"], 2)
    control = round(effects["control"], 2)
    communism = round(effects["communism"], 2)
    if not delta:
        return f"п {government} э {economy} в {military} н {control} к " \
               f"{communism}"
    else:
        signs = [
            "+" if government >= 0 else "",
            "+" if economy >= 0 else "",
            "+" if military >= 0 else "",
            "+" if control >= 0 else "",
            "+" if communism >= 0 else ""
        ]
        return f"\n Политическая мощь: {signs[0]}{government}\n" \
               f"Эконмическая мощь: {signs[1]}{economy}\n" \
               f"Военная мощь: {signs[2]}{military}\n" \
               f"Контроль над народом: {signs[3]}{control}\n" \
               f"Коммунизм: {signs[4]}{communism}"


def get_records():
    with open(f"/home/{site}/mysite/records.json", "r",
              encoding="utf8") as file:
        records = json.loads(file.read())
    winners = list(filter(lambda user: user[1][0] == "communism max",
                          records.items()))
    winners = list(sorted(winners, key=lambda user: user[1][1]))[:10]
    winners_number = 10
    header = "\t Имя игрока \t Кол-во ходов"
    winners = list(map(lambda user: f"\t{user[0]} \t\t\t {user[1][1]}",
                       winners))
    if len(winners) < winners_number:
        winners += ["\t - \t\t\t -"] * (winners_number - len(winners))
    result = "\n".join([header] + winners)
    return result


if __name__ == '__main__':
    app.run()