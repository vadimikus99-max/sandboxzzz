[app]
title = Sandbox2D
package.name = sandbox2d
package.domain = org.mygame
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.exclude_dirs = tests, bin, .buildozer, __pycache__, .git, venv, assets/large
version = 1.0.0
requirements = python3,kivy,numpy,numba,pyjnius
# orientation = landscape
# fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[android]
# api = 31
minapi = 21
ndk_api = 21
# ndk_version = 25b # Фиксируй версию NDK, иначе сломается numba
# Используем свежий NDK для поддержки aarch64
ndk_version = 26b
archs = arm64-v8a, armeabi-v7a
# permissions = INTERNET, VIBRATE
# services = 

# КРИТИЧНО для Numba/Numpy: нужно включить shared libs и разрешить JIT
# Numba на Android требует executable memory (PROT_EXEC).
# По дефолту Android запрещает RWX страницы (W^X).
# ВАРИАНТ 1: Собрать Numba в режиме AOT (Ahead Of Time) - СЛОЖНО.
# ВАРИАНТ 2 (ХАК): Добавить флаг линкера -z execstack (включает исполнение стека/кучи).
# Buildozer позволяет это через:
android.add_ldflags = -z execstack
# ИЛИ через python-for-android recipe patching (сложнее).
# Без -z execstack Numba упадет с "mmap: Permission denied" при первой компиляции.

# Увеличиваем память для сборки (gradle)
android.gradle_dependencies = 
android.enable_androidx = True
# android.permissions = 

[p4a]
# p4a ветка с поддержкой свежего numpy/numba
# branch = master
# bootstrap = sdl2

[ios]
# Не трогаем
