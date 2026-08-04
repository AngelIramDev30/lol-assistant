ROLE_CHAMPIONS: dict[str, set[str]] = {
    "top": {
        "Aatrox", "Ambessa", "Camille", "Cho'Gath", "Darius",
        "Dr. Mundo", "Fiora", "Gangplank", "Garen", "Gnar",
        "Gwen", "Illaoi", "Irelia", "Jax", "Jayce", "K'Sante",
        "Kayle", "Kennen", "Kled", "Malphite", "Mordekaiser",
        "Nasus", "Olaf", "Ornn", "Pantheon", "Poppy", "Quinn",
        "Renekton", "Riven", "Sett", "Shen", "Singed", "Sion",
        "Tahm Kench", "Teemo", "Trundle", "Tryndamere",
        "Udyr", "Urgot", "Vayne", "Volibear", "Warwick",
        "Wukong", "Yone", "Yorick",
    },
    "jungle": {
        "Amumu", "Bel'Veth", "Briar", "Diana", "Ekko", "Elise",
        "Evelynn", "Fiddlesticks", "Graves", "Hecarim", "Ivern",
        "Jarvan IV", "Karthus", "Kayn", "Kha'Zix", "Kindred",
        "Lee Sin", "Lillia", "Master Yi", "Nidalee", "Nocturne",
        "Nunu & Willump", "Rammus", "Rek'Sai", "Rengar", "Sejuani",
        "Shaco", "Shyvana", "Skarner", "Taliyah", "Udyr", "Vi",
        "Viego", "Volibear", "Warwick", "Wukong", "Xin Zhao", "Zac",
    },
    "middle": {
        "Ahri", "Akali", "Akshan", "Anivia", "Annie", "Aurelion Sol",
        "Azir", "Cassiopeia", "Diana", "Ekko", "Fizz", "Galio",
        "Hwei", "Kassadin", "Katarina", "LeBlanc", "Lissandra",
        "Lux", "Malzahar", "Naafiri", "Neeko", "Orianna", "Qiyana",
        "Ryze", "Swain", "Syndra", "Taliyah", "Talon", "Twisted Fate",
        "Veigar", "Vel'Koz", "Vex", "Viktor", "Vladimir", "Xerath",
        "Yasuo", "Yone", "Zed", "Zoe",
    },
    "bottom": {
        "Aphelios", "Ashe", "Caitlyn", "Corki", "Draven", "Ezreal",
        "Jhin", "Jinx", "Kai'Sa", "Kalista", "Kog'Maw", "Lucian",
        "Miss Fortune", "Nilah", "Samira", "Senna", "Sivir",
        "Smolder", "Tristana", "Twitch", "Varus", "Vayne", "Xayah",
        "Zeri",
    },
    "utility": {
        "Alistar", "Bard", "Blitzcrank", "Brand", "Braum", "Janna",
        "Karma", "Leona", "Lulu", "Lux", "Maokai", "Milio", "Morgana",
        "Nami", "Nautilus", "Neeko", "Pyke", "Rakan", "Rell", "Renata Glasc",
        "Senna", "Seraphine", "Sona", "Soraka", "Swain", "Tahm Kench",
        "Taric", "Thresh", "Vel'Koz", "Xerath", "Yuumi", "Zilean", "Zyra",
    },
}

ROLE_ALIASES: dict[str, str] = {
    "mid": "middle",
    "middle": "middle",
    "adc": "bottom",
    "bot": "bottom",
    "bottom": "bottom",
    "support": "utility",
    "sup": "utility",
    "utility": "utility",
    "jg": "jungle",
    "jungle": "jungle",
    "top": "top",
}


def normalize_role(role: str | None) -> str | None:
    if not role:
        return None

    return ROLE_ALIASES.get(role.strip().lower())


def filter_champions_by_role(
    champions: list[dict],
    role: str | None,
) -> list[dict]:
    normalized_role = normalize_role(role)

    if normalized_role is None:
        return champions

    allowed_names = ROLE_CHAMPIONS.get(normalized_role)

    if not allowed_names:
        return champions

    return [
        champion
        for champion in champions
        if champion.get("championName") in allowed_names
    ]
