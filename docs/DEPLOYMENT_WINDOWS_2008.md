# 🚀 Развертывание на Windows Server 2008 R2

Подробная инструкция по установке и настройке проекта Kharkiv Repairs System на Windows Server 2008 R2 с нуля.

## 📋 Предварительные требования

- Windows Server 2008 R2 (64-bit)
- Доступ к интернету
- Права администратора
- Минимум 4 GB RAM, 20 GB свободного места

## 🛠️ Шаг 1: Установка Python 3.11

### 1.1 Скачивание Python

1. Откройте браузер (Internet Explorer или установите современный браузер)
2. Перейдите на https://www.python.org/downloads/windows/
3. Скачайте **Python 3.11.x** (последняя стабильная версия)
4. Выберите **Windows installer (64-bit)** - файл `python-3.11.x-amd64.exe`

### 1.2 Установка Python

1. Запустите скачанный установщик от имени администратора
2. **ВАЖНО**: Поставьте галочку "Add Python to PATH"
3. Выберите "Install Now"
4. Дождитесь завершения установки

### 1.3 Проверка установки

Откройте Command Prompt (cmd) и выполните:

```cmd
python --version
pip --version
```

Должны увидеть версии Python 3.11.x и pip.

## 🛠️ Шаг 2: Установка Node.js

### 2.1 Скачивание Node.js

1. Перейдите на https://nodejs.org/
2. Скачайте **LTS версию** для Windows (64-bit)
3. Файл будет называться `node-v18.x.x-x64.msi` или похоже

### 2.2 Установка Node.js

1. Запустите .msi файл от имени администратора
2. Следуйте мастеру установки (все настройки по умолчанию)
3. Убедитесь, что выбрана опция "Add to PATH"

### 2.3 Проверка установки

```cmd
node --version
npm --version
```

## 🛠️ Шаг 3: Установка Git

### 3.1 Скачивание Git

1. Перейдите на https://git-scm.com/download/win
2. Скачайте Git для Windows (64-bit)

### 3.2 Установка Git

1. Запустите установщик от имени администратора
2. Используйте настройки по умолчанию
3. **Важно**: выберите "Git from the command line and also from 3rd-party software"

### 3.3 Проверка установки

```cmd
git --version
```

## 🛠️ Шаг 4: Установка UV (Python Package Manager)

```cmd
pip install uv
```

Проверка:

```cmd
uv --version
```

## 📁 Шаг 5: Подготовка проекта

### 5.1 Создание рабочей директории

```cmd
cd C:\
mkdir Projects
cd Projects
```

### 5.2 Клонирование проекта

Если у вас есть Git репозиторий:

```cmd
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> kharkiv-repairs
cd kharkiv-repairs
```

Или скопируйте файлы проекта в папку `C:\Projects\kharkiv-repairs\`

## 🛠️ Шаг 6: Настройка Backend

### 6.1 Установка Python зависимостей

```cmd
cd C:\Projects\kharkiv-repairs
uv sync
```

### 6.2 Создание базы данных

База данных SQLite создастся автоматически при первом запуске.

### 6.3 Применение миграций (если есть)

```cmd
uv run alembic upgrade head
```

## 🛠️ Шаг 7: Настройка Frontend

### 7.1 Установка JavaScript зависимостей

```cmd
npm install
```

### 7.2 Сборка для продакшена

```cmd
npm run build
```

## 🚀 Шаг 8: Запуск приложения

### 8.1 Запуск Backend

Откройте первое окно Command Prompt:

```cmd
cd C:\Projects\kharkiv-repairs
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 8.2 Запуск Frontend (для разработки)

Откройте второе окно Command Prompt:

```cmd
cd C:\Projects\kharkiv-repairs
npm run dev -- --host 0.0.0.0 --port 3000
```

## 🌐 Шаг 9: Настройка файрвола Windows

### 9.1 Открытие портов

1. Откройте "Windows Firewall with Advanced Security"
2. Создайте новые правила для входящих подключений:

**Для Backend (порт 8000):**

- Тип правила: Port
- Protocol: TCP
- Port: 8000
- Action: Allow the connection
- Profile: все профили
- Name: "Kharkiv Repairs Backend"

**Для Frontend (порт 3000):**

- Тип правила: Port
- Protocol: TCP
- Port: 3000
- Action: Allow the connection
- Profile: все профили
- Name: "Kharkiv Repairs Frontend"

## 🔧 Шаг 10: Создание Windows Services (Опционально)

### 10.1 Установка NSSM (Non-Sucking Service Manager)

1. Скачайте NSSM с https://nssm.cc/download
2. Распакуйте в `C:\nssm\`
3. Добавьте `C:\nssm\win64\` в PATH

### 10.2 Создание службы для Backend

```cmd
nssm install KharkivRepairsBackend
```

В открывшемся окне:

- Path: `C:\Projects\kharkiv-repairs\venv\Scripts\uvicorn.exe`
- Startup directory: `C:\Projects\kharkiv-repairs`
- Arguments: `backend.app.main:app --host 0.0.0.0 --port 8000`

### 10.3 Создание службы для Frontend

Сначала создайте bat файл `C:\Projects\kharkiv-repairs\start-frontend.bat`:

```batch
@echo off
cd /d C:\Projects\kharkiv-repairs
npm run dev -- --host 0.0.0.0 --port 3000
```

Затем:

```cmd
nssm install KharkivRepairsFrontend
```

- Path: `C:\Projects\kharkiv-repairs\start-frontend.bat`
- Startup directory: `C:\Projects\kharkiv-repairs`

### 10.4 Запуск служб

```cmd
nssm start KharkivRepairsBackend
nssm start KharkivRepairsFrontend
```

## 🌍 Шаг 11: Проверка работы

### 11.1 Локальная проверка

На сервере откройте браузер и перейдите:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### 11.2 Внешняя проверка

С другого компьютера в сети:

- Frontend: http://IP_СЕРВЕРА:3000
- Backend API: http://IP_СЕРВЕРА:8000/docs

## 🔧 Шаг 12: Настройка для продакшена

### 12.1 Использование IIS (рекомендуется)

1. Установите IIS через "Server Manager" → "Roles" → "Web Server (IIS)"
2. Установите IIS URL Rewrite Module
3. Установите HttpPlatformHandler

### 12.2 Настройка IIS для Frontend

1. Создайте новый сайт в IIS
2. Укажите путь к `C:\Projects\kharkiv-repairs\dist\`
3. Настройте порт 80 или 443 (для HTTPS)

### 12.3 Настройка reverse proxy для Backend

Создайте `web.config` в корне сайта:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="API Proxy" stopProcessing="true">
          <match url="^api/(.*)" />
          <action type="Rewrite" url="http://localhost:8000/api/{R:1}" />
        </rule>
        <rule name="Frontend" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

## 🔍 Шаг 13: Устранение неполадок

### 13.1 Проблемы с Python

```cmd
# Переустановка uv
pip uninstall uv
pip install uv

# Очистка кэша
uv cache clean
```

### 13.2 Проблемы с Node.js

```cmd
# Очистка кэша npm
npm cache clean --force

# Переустановка зависимостей
rmdir /s node_modules
npm install
```

### 13.3 Проблемы с портами

```cmd
# Проверка занятых портов
netstat -an | find "8000"
netstat -an | find "3000"
```

### 13.4 Логи приложения

Backend логи будут в консоли или в Event Viewer если используете службы.

## 📋 Шаг 14: Мониторинг и обслуживание

### 14.1 Автозапуск служб

Убедитесь, что службы настроены на автоматический запуск:

```cmd
sc config KharkivRepairsBackend start= auto
sc config KharkivRepairsFrontend start= auto
```

### 14.2 Резервное копирование

Создайте bat файл для резервного копирования базы данных:

```batch
@echo off
set BACKUP_DIR=C:\Backups\KharkivRepairs
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

copy "C:\Projects\kharkiv-repairs\db\*.db" "%BACKUP_DIR%\backup_%DATE%.db"
```

## ✅ Финальная проверка

После завершения всех шагов у вас должно быть:

1. ✅ Python 3.11 установлен и работает
2. ✅ Node.js установлен и работает
3. ✅ Git установлен
4. ✅ UV установлен
5. ✅ Проект склонирован и настроен
6. ✅ Backend запущен на порту 8000
7. ✅ Frontend запущен на порту 3000
8. ✅ Файрвол настроен
9. ✅ Приложение доступно извне
10. ✅ (Опционально) Службы Windows настроены

## 🆘 Поддержка

Если возникают проблемы:

1. Проверьте логи в консоли
2. Убедитесь, что все порты открыты
3. Проверьте права доступа к файлам
4. Убедитесь, что все зависимости установлены

---

**🎉 Поздравляем! Проект Kharkiv Repairs System успешно развернут на Windows Server 2008 R2!**
