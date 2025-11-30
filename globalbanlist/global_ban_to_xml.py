#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Ban → serveradmin.xml (автообновление)
-
Скрипт получает список игроков онлайн через API,
сверяет их с глобальным banlist.xml на GitHub
и добавляет совпадения (Steam/EOS) в <blacklist> секцию serveradmin.xml.
Запускается в цикле раз в час.
--------------------------------------------
Global Ban → serveradmin.xml (auto-update)
-
The script gets a list of online players via API,
compares them with global banlist.xml on GitHub,
and adds matches (Steam/EOS) to <blacklist> section of serveradmin.xml.
Runs in a loop once per hour.
"""

import requests
import xml.etree.ElementTree as ET
import logging
import time

PLAYERS_API = "http://your link to the map/api/getplayersonline"
BANLIST_URL = "https://raw.githubusercontent.com/sLimLong/banlist/main/banlist.xml"
XML_FILE = "serveradmin.xml"

logging.basicConfig(
    filename="ban_to_xml.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def normalize_id(platform, userid: str) -> str:
    """Привести ID к единому формату (убираем префиксы Steam_/EOS_)"""
    if not userid:
        return ""
    if platform == "Steam":
        return userid.replace("Steam_", "").strip()
    if platform == "EOS":
        return userid.replace("EOS_", "").strip()
    return userid.strip()

def get_online_players():
    """Получить список игроков онлайн через API (Steam + EOS)"""
    try:
        resp = requests.get(PLAYERS_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        players = []

        for p in data:
            # Steam
            if "steamid" in p:
                sid = normalize_id("Steam", p["steamid"])
                players.append(("Steam", sid))
            # EOS (crossplatformid)
            if "crossplatformid" in p:
                eid = normalize_id("EOS", p["crossplatformid"])
                players.append(("EOS", eid))

        print("RAW API DATA:", data)  # отладка
        print("Игроки онлайн (нормализованные):", players)

        logging.info(f"Получено {len(players)} игроков онлайн: {players}")
        return players
    except Exception as e:
        logging.error(f"Ошибка получения игроков: {e}")
        return []

def get_global_banlist():
    """Загрузить banlist.xml и извлечь Steam/EOS ID"""
    try:
        resp = requests.get(BANLIST_URL, timeout=10)
        resp.raise_for_status()
        xml_content = resp.text

        root = ET.fromstring(xml_content)
        ban_ids = set()

        for elem in root.findall(".//user"):
            platform = elem.get("platform")
            userid = elem.get("userid")
            if platform in ("Steam", "EOS") and userid:
                ban_ids.add((platform, normalize_id(platform, userid)))

        for elem in root.findall(".//blacklisted"):
            platform = elem.get("platform")
            userid = elem.get("userid")
            if platform in ("Steam", "EOS") and userid:
                ban_ids.add((platform, normalize_id(platform, userid)))

        # убрали print("Бан‑лист:", ban_ids)
        return ban_ids
    except Exception as e:
        print(f"❌ Ошибка загрузки banlist.xml: {e}")
        return set()


def update_xml(banned_ids):
    """
    Добавить совпадения в serveradmin.xml
    banned_ids: список кортежей (platform, userid)
    """
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Ошибка чтения {XML_FILE}: {e}")
        return

    # Найти или создать секцию <blacklist>
    blacklist = root.find("blacklist")
    if blacklist is None:
        blacklist = ET.SubElement(root, "blacklist")

    # Добавляем новые записи
    for platform, bid in banned_ids:
        exists = any(
            entry.get("userid") == bid and entry.get("platform") == platform
            for entry in blacklist.findall("blacklisted")
        )
        if not exists:
            entry = ET.SubElement(blacklist, "blacklisted")
            entry.set("platform", platform)
            entry.set("userid", bid)
            entry.set("name", "GlobalBan")
            entry.set("reason", "Global banlist match")
            print(f"🚫 Добавлен {platform}:{bid} в blacklist")

    # Сохраняем изменения
    try:
        tree.write(XML_FILE, encoding="UTF-8", xml_declaration=True)
        print(f"✅ Файл {XML_FILE} обновлён")
    except Exception as e:
        print(f"❌ Ошибка записи {XML_FILE}: {e}")


def run_check():
    logging.info("Запуск проверки игроков онлайн.../Launching player verification online...")
    players = get_online_players()
    banlist = get_global_banlist()

    banned = [p for p in players if p in banlist]
    if banned:
        print("🚫 Найдены совпадения:/Matches found:", banned)
        update_xml(banned)
    else:
        print("✅ Совпадений не найдено/No matches found")

if __name__ == "__main__":
    while True:
        run_check()
        print("⏳ Ожидание 1 час до следующей проверки.../Wait for 1 hour before the next check...")
        time.sleep(3600)

