# Телеграмм бот

## 1) Подключение к серверу

```bash 
ssh root@IP_СЕРВЕРА  
ввести пароль
```

---

## 2) Подготовка сервера

Установим необходимые пакеты (для Ubuntu/Debian):
```bash
sudo apt update 
sudo apt install -y python3 python3-venv python3-pip git screen
``` 

---

## 3) Структура проекта

Скачаем проект и создадим окружение:

```bash
mkdir -p ~/apps cd ~/apps 
git clone https://github.com/Madkond/reply_bot.git 
cd mybot  

python3 -m venv .venv 
source .venv/bin/activate
```

Устанавливаем зависимости:

```bash
pip install --upgrade pip 
pip install -r requirements.txt
```

---

## 4) Переменные окружения

Создаём файл `.env` в папке проекта:

```bash 
nano ~/apps/mybot/.env
```

Надо получить токен `@BotFather` в телеграмм :

<img src="[Pasted image 20250905144859.png](https://drive.google.com/file/d/1Vz3pG9ZjhqB3tZnnnmzjGI2S02ujNJgB/view?usp=sharing)" width="50%" />

<img src="Pasted image 20250905144909.png" width="50%" />


##### Добавить в .env файл токен:
```bash 
BOT_TOKEN=1234567890:ABCDEF_ВАШ_ТОКЕН
```

---

## 5) Запуск в фоне через `screen`

### Создание сессии

`cd ~/apps/mybot screen -S mybot`

Внутри `screen` запускаем:

`python3 main.py`

Отделиться:  
`Ctrl+A`, затем `D`

---

### Управление `screen`

- **Список сессий:**
    
    `screen -ls`
    
- **Подключиться к сессии:**
    
    `screen -r mybot`
    
- **Выйти (отделиться):**  
    `Ctrl+A`, затем `D`
    
- **Остановить сессию:**
    
    `screen -S mybot -X quit`
    

---

## 6) Первичная настройка бота
1. Добавить бота как обработчика в разделе "Телеграмм для бизнеса"
![[Pasted image 20250905145438.png]]
2. Зайти в бота в Telegram и ввести команду `/start`.
![[Pasted image 20250905145101.png]]
3. Добавить бота админом в нужный канал.
![[Pasted image 20250904090433.png]]
4. После этого бот начнёт пересылать сообщения.
