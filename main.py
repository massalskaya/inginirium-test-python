# подключаем библиотеки
import pygame
import os
import random
import sqlite3

# задаём размеры окна
SCREEN_WIDTH = 960
FIELD_WIDTH = 800  # игровое поле
FIELD_BEGIN = 200
HEIGHT = 600
RACKET_HEIGHT = 550  # высота ракетки
BORDER_X = 200  # граница м/д полем и счётом
FPS = 30  # частота: кадров в секунду

# Создаём игру и её окно
pygame.init()
pygame.mixer.init()  # для звука
screen = pygame.display.set_mode((SCREEN_WIDTH, HEIGHT))
pygame.display.set_caption("Арканоша")
clock = pygame.time.Clock()

# Цветовые константы
WHITE = (255, 255, 255)
AQUA = (0, 255, 255)
KHAKI = (240, 230, 140)
CORAL = (255, 127, 80)
YELLOWGREEN = (154, 205, 50)

# Выводим текст заданным цветом с заданным смещением
# относительно последней строки
TEXT_COL = 10


def printColorText(txt, color, x, y, size=20):
    global last_str_pos
    font = pygame.font.SysFont('Courier New', size, bold=True, italic=False)
    text = font.render(str(txt), True, color)
    screen.blit(text, (x, y))


# Рабочие папки: сама игра, графика
GAME_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(GAME_PATH, 'img')
# загружаем картинки
# и оптимизируем для игры
# convert_alpha, если надо учитывать прозрачный фон
ball_img = pygame.image.load(os.path.join(IMG_PATH, 'ball.png')).convert_alpha()
racket_img = pygame.image.load(os.path.join(IMG_PATH, 'bita.png')).convert_alpha()
back_img = pygame.image.load(os.path.join(IMG_PATH, 'back.png')).convert()
brick_blue_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_blue.png')).convert_alpha()
brick_lime_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_lime.png')).convert_alpha()
brick_orange_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_orange.png')).convert_alpha()
brick_pink_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_pink.png')).convert_alpha()
brick_red_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_red.png')).convert_alpha()
brick_yellow_img = pygame.image.load(os.path.join(IMG_PATH, 'brick_yellow.png')).convert_alpha()


# --------
# ОБЪЕКТЫ
# --------


# Класс - шарик
class Ball(pygame.sprite.Sprite):
    # инициализатор
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # картинка
        self.image = ball_img
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (FIELD_BEGIN + FIELD_WIDTH / 2, RACKET_HEIGHT - self.rect.height)
        # изменение координат шарика
        self.__dx = 6
        self.__dy = -5

    # Движение шарика и отражение от бортов
    # Левый борт - это граница м/д счётом и полем
    def update(self):
        self.rect.x += self.__dx
        self.rect.y += self.__dy
        # Проверяем, не столкнулись ли со стенами
        # Если столкнулись с вертикальной -
        # изменяем направление смещений по горизонтали
        # и наоборот
        if self.rect.left <= FIELD_BEGIN or self.rect.right >= SCREEN_WIDTH:
            self.__dx = -self.__dx
        if self.rect.top <= 0:
            self.__dy = -self.__dy
        # не даём падать вниз только при чите
        if cheatmode and self.rect.bottom >= HEIGHT:
            self.__dy = -self.__dy

    # Геттеры-сеттеры
    def get_dx(self):
        return self.__dx

    def get_dy(self):
        return self.__dy

    def set_dxdy(self, dx, dy):
        self.__dx = dx
        self.__dy = dy



# Приращение скорости ракетки
RACKET_DV = 4


# Класс - ракетка
class Racket(pygame.sprite.Sprite):
    # инициализатор
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = racket_img
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (FIELD_BEGIN + FIELD_WIDTH / 2, RACKET_HEIGHT)
        # изменение координат ракетки
        self.__dx = 0
        self.__dy = 0
        # скорость ракетки (может ускоряться и замедляться)
        self.__speed = 0

    # Движение ракетки - стрелками
    def update(self):
        self.rect.x += self.__speed
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            if self.__speed > 0:
                self.__speed = 0
            else:
                self.__speed = -RACKET_DV
        if keystate[pygame.K_RIGHT]:
            if self.__speed < 0:
                self.__speed = 0
            else:
                self.__speed = RACKET_DV
        self.rect.x += self.__speed
        # Не даём ракетке выехать за пределы поля
        if self.rect.x <= FIELD_BEGIN:
            self.rect.x = FIELD_BEGIN
            self.__speed = 0
        if self.rect.x + self.rect.width >= SCREEN_WIDTH:
            self.rect.x = SCREEN_WIDTH - self.rect.width
            self.__speed = 0

    # Геттеры-сеттеры
    def get_speed(self):
        return self.__speed


# Позиции кирпичей
BRICKS_FIRST_ROW = 50
BRICKS_FIRST_COL = 50
BRICKS_ROW_SIZE = 40
BRICKS_COL_SIZE = 100


# Класс - кирпич
class Brick(pygame.sprite.Sprite):
    # инициализатор
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # случайный цвет
        c = random.randint(1, 6)
        if c == 1:
            self.image = brick_blue_img
        elif c == 2:
            self.image = brick_lime_img
        elif c == 3:
            self.image = brick_orange_img
        elif c == 4:
            self.image = brick_pink_img
        elif c == 5:
            self.image = brick_red_img
        else:
            self.image = brick_yellow_img
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

    # Устанавливаем кирпич в позицию по координатам
    def setCoords(self, row, col):
        self.rect.center = (FIELD_BEGIN + BRICKS_FIRST_COL + (BRICKS_COL_SIZE * col) + BRICKS_COL_SIZE / 3,
                            BRICKS_FIRST_ROW + (BRICKS_ROW_SIZE * row) - BRICKS_ROW_SIZE / 2)


# Рисуем уровень из строк кирпичей
def printLevel():
    # очищаем уровень
    for item in bricks:
        item.kill()
    # рисуем уровень
    for i in range(6):
        for j in range(7):
            b = Brick()
            b.setCoords(i, j)
            sprites.add(b)
            bricks.add(b)


# --------
# БАЗА ДАННЫХ
# --------

# Создаём БД
def createDB():
    db_connect = sqlite3.connect('toplist.db')
    db_cursor = db_connect.cursor()
    # если пусто - создаём
    db_cursor.execute("CREATE TABLE IF NOT EXISTS toplist("
                      "pos INT PRIMARY KEY,"
                      "name TEXT,"
                      "score INT);")
    db_connect.commit()


# Очищаем всю БД
def delDB():
    db_connect = sqlite3.connect('toplist.db')
    db_cursor = db_connect.cursor()
    db_cursor.execute("DELETE FROM toplist;")
    db_connect.commit()


# Загружаем топ-лист из базы
def getToplist():
    createDB()  # если базы нет - создаём
    db_connect = sqlite3.connect('toplist.db')
    db_cursor = db_connect.cursor()
    # Вытаскиваем данные
    db_cursor.execute("SELECT * FROM toplist;")
    res = db_cursor.fetchall()
    # но нам нужен другой вид списков
    toplist = []
    for i in range(len(res)):
        toplist.append([res[i][1], res[i][2], 0])
    return toplist


# Загружаем в БД топ-лист из 10 элементов
# (просто переписываем 10 первых)
def writeToplist(toplist):
    delDB()  # очищаем базу
    db_connect = sqlite3.connect('toplist.db')
    db_cursor = db_connect.cursor()
    if len(toplist) >= 10:
        finish = 10
    else:
        finish = len(toplist)
    query = "INSERT INTO toplist VALUES(?,?,?);"
    for i in range(finish):
        player = (i, toplist[i][0], toplist[i][1])
        db_cursor.execute(query, player)
        db_connect.commit()


# --------
# ИГРОВОЙ ПРОЦЕСС
# --------


# Объявляем группу спрайтов
sprites = pygame.sprite.Group()
ball = Ball()  # Наш шарик - экземпляр класса Ball
sprites.add(ball)
racket = Racket()  # И ракетка тоже экземпляр
sprites.add(racket)
# Рисуем уровень
bricks = pygame.sprite.Group()


# --------
# Начало игры - получаем имя игрока
def enterPlayerName():
    running = True
    # Игрок
    player_name = 'IGROK'
    cursor_color = (0, 0, 0)  # курсор - чтоб моргал
    # Цикл ввода имени
    # pygame не воспринимает русские буквы
    # и прописные, даже если зажат CapsLock
    # Все это надо обрабатывать вручную через коды
    while running:
        # FPS можно пониже
        clock.tick(5)
        # События: закрытие
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if len(player_name) > 0:
                        player_name = player_name[:len(player_name) - 1]
                elif event.key == pygame.K_KP_ENTER or event.key == pygame.K_RETURN:
                    return player_name
                else:
                    k = event.key
                    player_name += chr(event.key)
                    player_name = player_name.upper()
        # визуализация
        screen.fill((0, 0, 0))
        screen.blit(back_img, (0, 0))
        # Информация об игре
        panel = pygame.Rect(200, 100, SCREEN_WIDTH - 400, HEIGHT - 200)
        pygame.draw.rect(screen, (20, 20, 20), panel, 0)
        printColorText('ИГРА', CORAL, 390, 150, 25)
        printColorText('АРКАНОША', CORAL, 390, 180, 40)
        # Окно запроса имени игрока
        printColorText('Введите ваше имя:', YELLOWGREEN, 250, 300, 20)
        enter_win = pygame.Rect(250, 340, 300, 40)
        pygame.draw.rect(screen, (0, 0, 0), enter_win, 0)
        printColorText('По окончании ввода', WHITE, 250, 400, 16)
        printColorText('нажмите [Enter]', WHITE, 250, 420, 16)
        # типа курсор
        if cursor_color == (0, 0, 0):
            cursor_color = (255, 255, 255)
        else:
            cursor_color = (0, 0, 0)
        cursor = pygame.Rect(255 + len(player_name) * 15, 345, 1, 20)
        pygame.draw.rect(screen, cursor_color, cursor, 0)
        # выводим имя игрока
        printColorText(player_name, YELLOWGREEN, 255, 345, 20)
        # Флипаем экран
        pygame.display.flip()


# Чит! 0 на цифровой клавиатуре
cheatmode = False


# --------
# Игровой процесс
def playGame():
    # Игрок и оппоненты
    # 3-й параметр = 0 для старых игроков и 1 для текущего
    # toplist = []
    toplist = getToplist()  # получили из базы
    player = [player_name, 0, 1]
    toplist.append(player)
    # сортируем по убыванию очков
    toplist.sort(key=lambda player: -player[1])

    running = True
    # Уровень
    level = 1
    global cheatmode

    # Ставим шарик на место
    ball.rect.center = (FIELD_BEGIN + FIELD_WIDTH / 2, RACKET_HEIGHT - ball.rect.height)
    ball.set_dxdy(0,0)
    isInGame = False
    # Кирпичики
    printLevel()

    # Игровой цикл (бесконечный)
    while running:
        # Держим цикл на правильной скорости
        clock.tick(FPS)

        # Ввод (события)
        for event in pygame.event.get():
            # Проверяем, не закрывает ли юзер окно
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_KP0:
                    cheatmode = not cheatmode
                if not isInGame:  # шарик начинает двигаться, если стоял
                    isInGame = True
                    ball.set_dxdy(6, -5)

        # Обновление
        sprites.update()

        # Визуализация (сборка игрового поля):
        # - Рендеринг
        screen.fill((0, 0, 0))
        screen.blit(back_img, (0, 0))
        # Отрисовываем все спрайты
        sprites.draw(screen)

        # ОТРИСОВЫВАЕМ СЧЁТ
        # Граница м/д игровым полем и счётом
        border = pygame.Rect(BORDER_X, 0, 1, HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), border, 0)
        printColorText('СЧЁТ', WHITE, TEXT_COL, 50, 30)
        printColorText('----', WHITE, TEXT_COL, 85, 30)
        # Имена и счёт
        pos = 120
        for i in range(len(toplist)):
            if toplist[i][2] == 1:
                c = KHAKI
            else:
                c = AQUA
            s = toplist[i][0] + ': ' + str(toplist[i][1])
            printColorText(s, c, TEXT_COL, pos + 25 * i)
        # Уровень
        printColorText('УРОВЕНЬ ' + str(level), CORAL, TEXT_COL, 450, 20)
        # Подсказки
        if len(bricks) == 42:
            printColorText('Нажмите', WHITE, TEXT_COL, 520, 16)
            printColorText('что-нибудь', WHITE, TEXT_COL, 540, 16)
            printColorText('для начала', WHITE, TEXT_COL, 560, 16)
        if level > 1 and len(bricks) > 30 and len(bricks)!=42:
            printColorText('Ура! Вы перешли', WHITE, TEXT_COL, 520, 16)
            printColorText('на новый уровень!', WHITE, TEXT_COL, 540, 16)
        if level == 1 and len(bricks) > 30 and len(bricks)!=42:
            printColorText('Управление', WHITE, TEXT_COL, 520, 16)
            printColorText('стрелками', WHITE, TEXT_COL, 540, 16)
            printColorText('<- и ->', WHITE, TEXT_COL, 560, 16)
        if len(bricks) < 10:
            printColorText('Поднажмите!', WHITE, TEXT_COL, 520, 16)
        # чит-режим
        if cheatmode:
            cheatpanel = pygame.Rect(BORDER_X, HEIGHT - 1, SCREEN_WIDTH - BORDER_X, 1)
            pygame.draw.rect(screen, YELLOWGREEN, cheatpanel, 0)

        # Отслеживаем столкновение ракетки и шарика
        if racket.rect.colliderect(ball.rect):
            ball.rect.bottom = racket.rect.top
            ball.set_dxdy(-ball.get_dx() + racket.get_speed(), -ball.get_dy() + racket.get_speed())
        # Отслеживаем столкновение шарика и кирпича
        # True - при столкновении удаляем кирпич
        hits = pygame.sprite.spritecollide(ball, bricks, True)
        if hits:
            for i in range(len(toplist)):
                if toplist[i][2] == 1:  # это игрок
                    toplist[i][1] += 1
                    toplist.sort(key=lambda player: -player[1])
            # и пусть шарик отражается от удалённого кирпича
            ball.set_dxdy(ball.get_dx(), -ball.get_dy())
            # а если все кирпичи закончились - начинаем новый уровень
            if len(bricks) == 0:
                level += 1
                printLevel()
                racket.rect.center = (FIELD_BEGIN + FIELD_WIDTH / 2, RACKET_HEIGHT)
                ball.rect.center = (FIELD_BEGIN + FIELD_WIDTH / 2, RACKET_HEIGHT - ball.rect.height)
                ball.set_dxdy(0, 0)
                isInGame = False
        # шарик выпал вниз - конец игры
        if ball.rect.top >= HEIGHT:
            # сбрасываем результаты в базу
            writeToplist(toplist)
            # возвращаем счёт игрока
            for i in range(len(toplist)):
                if toplist[i][2] == 1:
                    return toplist[i][1]

        # - После отрисовки текущего кадра переворачиваем экран
        pygame.display.flip()


# --------
# Если игрок проиграл,
# можно начать заново
def gameOver(score):
    running = True
    while running:
        # FPS можно пониже
        clock.tick(5)
        # События: закрытие
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    return 1
                else:
                    exit()
        # визуализация
        screen.fill((0, 0, 0))
        screen.blit(back_img, (0, 0))
        # Информация об игре
        panel = pygame.Rect(200, 100, SCREEN_WIDTH - 400, HEIGHT - 200)
        pygame.draw.rect(screen, (0, 0, 0), panel, 0)
        printColorText('ИГРА ОКОНЧЕНА', YELLOWGREEN, 250, 150, 25)
        printColorText('Ваш результат: ', KHAKI, 250, 190, 25)
        printColorText(str(score), CORAL, 480, 185, 35)
        printColorText('Чтобы начать игру заново,', WHITE, 250, 270, 20)
        printColorText('нажмите [Enter]', WHITE, 250, 300, 20)
        # Флипаем экран
        pygame.display.flip()


player_name = enterPlayerName()
inGame = True
while inGame:
    score = playGame()
    gameOver(score)
    foolFlag = 0


# Юзер закрыл окно - завершаем программу
# (выключаем pygame)
pygame.quit()
