FRONTLINE_CHAMPIONS: set[str] = {
    "Alistar", "Amumu", "Blitzcrank", "Braum", "Cho'Gath",
    "Dr. Mundo", "Galio", "Garen", "Gragas", "Jarvan IV",
    "K'Sante", "Leona", "Malphite", "Maokai", "Nautilus",
    "Nunu & Willump", "Ornn", "Poppy", "Rammus", "Rell",
    "Renekton", "Sejuani", "Sett", "Shen", "Sion",
    "Skarner", "Tahm Kench", "Taric", "Thresh", "Udyr",
    "Urgot", "Volibear", "Warwick", "Zac",
}

ENGAGE_CHAMPIONS: set[str] = {
    "Alistar", "Amumu", "Ashe", "Blitzcrank", "Diana",
    "Galio", "Gnar", "Gragas", "Jarvan IV", "Kennen",
    "Leona", "Lissandra", "Malphite", "Maokai", "Nautilus",
    "Neeko", "Nocturne", "Nunu & Willump", "Ornn", "Poppy",
    "Pyke", "Rakan", "Rell", "Renata Glasc", "Sejuani",
    "Seraphine", "Sion", "Skarner", "Thresh", "Vi",
    "Wukong", "Zac",
}

PEEL_CHAMPIONS: set[str] = {
    "Alistar", "Bard", "Braum", "Galio", "Ivern",
    "Janna", "Karma", "Lulu", "Milio", "Morgana",
    "Nami", "Nautilus", "Orianna", "Poppy", "Rakan",
    "Renata Glasc", "Seraphine", "Shen", "Sona", "Soraka",
    "Tahm Kench", "Taric", "Thresh", "Yuumi", "Zilean",
}

MAGIC_DAMAGE_CHAMPIONS: set[str] = {
    "Ahri", "Akali", "Amumu", "Anivia", "Annie",
    "Aurelion Sol", "Brand", "Cassiopeia", "Diana", "Ekko",
    "Elise", "Evelynn", "Fiddlesticks", "Fizz", "Galio",
    "Gwen", "Hwei", "Karthus", "Kassadin", "Katarina",
    "Kennen", "LeBlanc", "Lillia", "Lissandra", "Lux",
    "Malzahar", "Mordekaiser", "Morgana", "Neeko", "Orianna",
    "Rumble", "Ryze", "Seraphine", "Swain", "Syndra",
    "Taliyah", "Twisted Fate", "Veigar", "Vel'Koz", "Vex",
    "Viktor", "Vladimir", "Xerath", "Ziggs", "Zoe", "Zyra",
}

PHYSICAL_DAMAGE_CHAMPIONS: set[str] = {
    "Aatrox", "Akshan", "Aphelios", "Ashe", "Caitlyn",
    "Camille", "Darius", "Draven", "Ezreal", "Fiora",
    "Gangplank", "Graves", "Illaoi", "Irelia", "Jax",
    "Jayce", "Jhin", "Jinx", "Kai'Sa", "Kalista",
    "Kha'Zix", "Kindred", "Kled", "Lee Sin", "Lucian",
    "Master Yi", "Miss Fortune", "Nilah", "Olaf", "Pantheon",
    "Qiyana", "Quinn", "Renekton", "Rengar", "Riven",
    "Samira", "Senna", "Sett", "Sivir", "Talon",
    "Tristana", "Tryndamere", "Twitch", "Varus", "Vayne",
    "Vi", "Viego", "Xayah", "Xin Zhao", "Yasuo",
    "Yone", "Zed", "Zeri",
}


def has_trait(
    champion_name: str,
    trait: str,
) -> bool:
    trait_sets = {
        "frontline": FRONTLINE_CHAMPIONS,
        "engage": ENGAGE_CHAMPIONS,
        "peel": PEEL_CHAMPIONS,
        "magic": MAGIC_DAMAGE_CHAMPIONS,
        "physical": PHYSICAL_DAMAGE_CHAMPIONS,
    }

    champions = trait_sets.get(trait)

    if champions is None:
        return False

    return champion_name in champions
