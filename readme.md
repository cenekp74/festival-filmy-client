Klient k systému automatického pouštění filmů (apf) na festivalu JSNO (jsno.cz). 

Soubory jsou pouštěny pomocí VLC (python-vlc). Je třeba mít nainstalovanou 64-bitovou verzi. Po spuštění filmu je okno automaticky nastaveno do popředí (pomocí pygetwindow) Mezi filmama se pouští spořic obrazovky - načte se stránka `/screensaver/<room>` na serveru (pomocí portable firefoxu - MUSÍ BÝT VE SLOŽCE FIREFOX - VIZ RELEASE). Na stránce je zvuk, ten se ale nemůže spustit bez user interakce - proto je po spuštění firefoxu simulován stist klávesy (pomocí pywinauto). 

Proč python? Python jsem si vybral zejména kvůli tomu, že má dobrou knihovnu pro propojení s vlc, což se mi zdá spolehlivější než používat méně otesovaný knihovny na přehrávání videí např. v rustu / C. Taky zbožňuju knihovnu requests. Další důvod je snadné ovládání počítače pomocí pywinauto. 

## logika
- start
- pokus o fetchnuti programu - pokud je uspesny ulozi se do config
- pokud neni v config ani program ani schedule, ceka 10s a pak restartuje
- pokus o vytvoreni schedule - pokud failne, znamena to ze neexistuje program a tudiz uz musi existovat schedule
- pokus o ziskani current day - pokud failne beru ten z config.py
- pokud current day neni 0, kontroluju pritomnost souboru a pousitim filmy (fce run())
- po dokonceni fce run ceka restart_delay sekund a pak se restartuje

### behavior fce run
- loopuje schedule
- pokud je cas vetsi nez cas kdy se mel spustit dany film o vic nez max_delay_time minut, ceka na dalsi cas
- pokud je cas vetsi nez cas kdy se mel spustit film o min nez max_delay_time minut, spusti film i tak
- pokud je cas mensi, pusti screensaver a ceka
- po spusteni filmu ceka na jeho skonceni - muze se stat, ze kdyz je soubor delsi nez ma byt, dalsi film se spusti se spozdenim (max max_delay_time min viz vyse) nebo vubec