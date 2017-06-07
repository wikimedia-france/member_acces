#!/usr/bin/env python3

import logging

from logging.handlers import RotatingFileHandler


def easylogger(logfile, level=logging.DEBUG, filesize=10000000):
    # création de l'objet logger qui va nous servir à écrire dans les logs
    logger = logging.getLogger()
    # on met le niveau du logger à DEBUG, comme ça il écrit tout
    logger.setLevel(level)

    # retrait des logs INFO de Requests qui squattent
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # création d'un formateur qui va ajouter le temps, le niveau
    # de chaque message quand on écrira un message dans le log
    FORMAT = '%(asctime)s :: %(levelname)s :: %(message)s'
    formatter = logging.Formatter(FORMAT)
    # création d'un handler qui va rediriger une écriture du log vers
    # un fichier en mode 'append', avec 1 backup et une taille max de 10Mo
    file_handler = RotatingFileHandler(logfile, 'a', filesize, 5)
    # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le
    # formateur créé précédement et on ajoute ce handler au logger
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # création d'un second handler qui va rediriger chaque écriture de log
    # sur la console
    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(level)
    logger.addHandler(steam_handler)

    return logger
