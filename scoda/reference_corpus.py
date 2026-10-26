"""Reference evaluation corpus for the committed workload files.

The workload files shipped in ``workloads/`` are built from the fact tables
below, so a reader can inspect a case and see the shape of a real evaluation
record: a natural-language query, a
reference answer, the source dataset, and the configuration level the case
belongs to.

The four dataset names match the public corpora used in the evaluation
(Natural Questions, TriviaQA, HotpotQA, OpenBookQA) and each family of
questions is written in the style of its dataset: single-fact lookups for
Natural Questions, trivia lookups for TriviaQA, two-hop compositions for
HotpotQA, and elementary science for OpenBookQA. The public corpora themselves
are not redistributed here; ``load_dataset`` reads them from a local data
directory when they are present.

    from scoda.reference_corpus import reference_corpus
    pairs = reference_corpus(500)
"""

from __future__ import annotations

from typing import Callable, Dict, List, Sequence, Tuple

from .datasets import CORPUS, QAPair

# --- fact tables -----------------------------------------------------------

# (country, capital, continent)
COUNTRIES: Tuple[Tuple[str, str, str], ...] = (
    ("France", "Paris", "Europe"),
    ("Japan", "Tokyo", "Asia"),
    ("Brazil", "Brasilia", "South America"),
    ("Canada", "Ottawa", "North America"),
    ("Kenya", "Nairobi", "Africa"),
    ("Australia", "Canberra", "Oceania"),
    ("India", "New Delhi", "Asia"),
    ("Egypt", "Cairo", "Africa"),
    ("Norway", "Oslo", "Europe"),
    ("Peru", "Lima", "South America"),
    ("Mexico", "Mexico City", "North America"),
    ("Thailand", "Bangkok", "Asia"),
    ("Morocco", "Rabat", "Africa"),
    ("Portugal", "Lisbon", "Europe"),
    ("Chile", "Santiago", "South America"),
    ("Cuba", "Havana", "North America"),
    ("Vietnam", "Hanoi", "Asia"),
    ("Ghana", "Accra", "Africa"),
    ("Austria", "Vienna", "Europe"),
    ("Argentina", "Buenos Aires", "South America"),
    ("Guatemala", "Guatemala City", "North America"),
    ("Nepal", "Kathmandu", "Asia"),
    ("Tunisia", "Tunis", "Africa"),
    ("Greece", "Athens", "Europe"),
    ("Uruguay", "Montevideo", "South America"),
    ("Jamaica", "Kingston", "North America"),
    ("Malaysia", "Kuala Lumpur", "Asia"),
    ("Senegal", "Dakar", "Africa"),
    ("Finland", "Helsinki", "Europe"),
    ("Ecuador", "Quito", "South America"),
    ("Panama", "Panama City", "North America"),
    ("Indonesia", "Jakarta", "Asia"),
    ("Ethiopia", "Addis Ababa", "Africa"),
    ("Ireland", "Dublin", "Europe"),
    ("Poland", "Warsaw", "Europe"),
    ("Philippines", "Manila", "Asia"),
    ("Nigeria", "Abuja", "Africa"),
    ("Sweden", "Stockholm", "Europe"),
    ("Colombia", "Bogota", "South America"),
    ("Costa Rica", "San Jose", "North America"),
    ("South Korea", "Seoul", "Asia"),
    ("Algeria", "Algiers", "Africa"),
    ("Denmark", "Copenhagen", "Europe"),
    ("Paraguay", "Asuncion", "South America"),
    ("Honduras", "Tegucigalpa", "North America"),
    ("Pakistan", "Islamabad", "Asia"),
    ("Uganda", "Kampala", "Africa"),
    ("Hungary", "Budapest", "Europe"),
    ("Venezuela", "Caracas", "South America"),
    ("Nicaragua", "Managua", "North America"),
    ("Bangladesh", "Dhaka", "Asia"),
    ("Zambia", "Lusaka", "Africa"),
    ("Romania", "Bucharest", "Europe"),
    ("New Zealand", "Wellington", "Oceania"),
    ("Iceland", "Reykjavik", "Europe"),
    ("Mongolia", "Ulaanbaatar", "Asia"),
    ("Tanzania", "Dodoma", "Africa"),
    ("Switzerland", "Bern", "Europe"),
    ("Fiji", "Suva", "Oceania"),
    ("Cambodia", "Phnom Penh", "Asia"),
    ("Zimbabwe", "Harare", "Africa"),
    ("Czech Republic", "Prague", "Europe"),
)

# (title, author, nationality)
WORKS: Tuple[Tuple[str, str, str], ...] = (
    ("Pride and Prejudice", "Jane Austen", "British"),
    ("Moby-Dick", "Herman Melville", "American"),
    ("War and Peace", "Leo Tolstoy", "Russian"),
    ("Don Quixote", "Miguel de Cervantes", "Spanish"),
    ("One Hundred Years of Solitude", "Gabriel Garcia Marquez", "Colombian"),
    ("Things Fall Apart", "Chinua Achebe", "Nigerian"),
    ("The Great Gatsby", "F. Scott Fitzgerald", "American"),
    ("Mrs Dalloway", "Virginia Woolf", "British"),
    ("Crime and Punishment", "Fyodor Dostoevsky", "Russian"),
    ("Madame Bovary", "Gustave Flaubert", "French"),
    ("The Metamorphosis", "Franz Kafka", "Czech"),
    ("Beloved", "Toni Morrison", "American"),
    ("Midnight's Children", "Salman Rushdie", "British"),
    ("The Tale of Genji", "Murasaki Shikibu", "Japanese"),
    ("Kokoro", "Natsume Soseki", "Japanese"),
    ("The Stranger", "Albert Camus", "French"),
    ("Nineteen Eighty-Four", "George Orwell", "British"),
    ("Brave New World", "Aldous Huxley", "British"),
    ("To Kill a Mockingbird", "Harper Lee", "American"),
    ("Jane Eyre", "Charlotte Bronte", "British"),
    ("Wuthering Heights", "Emily Bronte", "British"),
    ("Great Expectations", "Charles Dickens", "British"),
    ("Anna Karenina", "Leo Tolstoy", "Russian"),
    ("The Brothers Karamazov", "Fyodor Dostoevsky", "Russian"),
    ("Les Miserables", "Victor Hugo", "French"),
    ("The Divine Comedy", "Dante Alighieri", "Italian"),
    ("Faust", "Johann Wolfgang von Goethe", "German"),
    ("The Trial", "Franz Kafka", "Czech"),
    ("Ulysses", "James Joyce", "Irish"),
    ("Dubliners", "James Joyce", "Irish"),
    ("Waiting for Godot", "Samuel Beckett", "Irish"),
    ("Half of a Yellow Sun", "Chimamanda Ngozi Adichie", "Nigerian"),
    ("The God of Small Things", "Arundhati Roy", "Indian"),
    ("A Passage to India", "E. M. Forster", "British"),
    ("The Old Man and the Sea", "Ernest Hemingway", "American"),
    ("Invisible Man", "Ralph Ellison", "American"),
    ("The Handmaid's Tale", "Margaret Atwood", "Canadian"),
    ("Life of Pi", "Yann Martel", "Canadian"),
    ("Snow Country", "Yasunari Kawabata", "Japanese"),
    ("The Remains of the Day", "Kazuo Ishiguro", "British"),
    ("Blindness", "Jose Saramago", "Portuguese"),
    ("The House of the Spirits", "Isabel Allende", "Chilean"),
    ("Pedro Paramo", "Juan Rulfo", "Mexican"),
    ("Season of Migration to the North", "Tayeb Salih", "Sudanese"),
    ("Nervous Conditions", "Tsitsi Dangarembga", "Zimbabwean"),
)

# (element, symbol, atomic number, periodic-table category)
ELEMENTS: Tuple[Tuple[str, str, int, str], ...] = (
    ("hydrogen", "H", 1, "nonmetal"),
    ("helium", "He", 2, "noble gas"),
    ("lithium", "Li", 3, "alkali metal"),
    ("beryllium", "Be", 4, "alkaline earth metal"),
    ("boron", "B", 5, "metalloid"),
    ("carbon", "C", 6, "nonmetal"),
    ("nitrogen", "N", 7, "nonmetal"),
    ("oxygen", "O", 8, "nonmetal"),
    ("fluorine", "F", 9, "halogen"),
    ("neon", "Ne", 10, "noble gas"),
    ("sodium", "Na", 11, "alkali metal"),
    ("magnesium", "Mg", 12, "alkaline earth metal"),
    ("aluminium", "Al", 13, "post-transition metal"),
    ("silicon", "Si", 14, "metalloid"),
    ("phosphorus", "P", 15, "nonmetal"),
    ("sulfur", "S", 16, "nonmetal"),
    ("chlorine", "Cl", 17, "halogen"),
    ("argon", "Ar", 18, "noble gas"),
    ("potassium", "K", 19, "alkali metal"),
    ("calcium", "Ca", 20, "alkaline earth metal"),
    ("titanium", "Ti", 22, "transition metal"),
    ("chromium", "Cr", 24, "transition metal"),
    ("manganese", "Mn", 25, "transition metal"),
    ("iron", "Fe", 26, "transition metal"),
    ("cobalt", "Co", 27, "transition metal"),
    ("nickel", "Ni", 28, "transition metal"),
    ("copper", "Cu", 29, "transition metal"),
    ("zinc", "Zn", 30, "transition metal"),
    ("selenium", "Se", 34, "nonmetal"),
    ("bromine", "Br", 35, "halogen"),
    ("krypton", "Kr", 36, "noble gas"),
    ("silver", "Ag", 47, "transition metal"),
    ("tin", "Sn", 50, "post-transition metal"),
    ("iodine", "I", 53, "halogen"),
    ("xenon", "Xe", 54, "noble gas"),
    ("barium", "Ba", 56, "alkaline earth metal"),
    ("tungsten", "W", 74, "transition metal"),
    ("platinum", "Pt", 78, "transition metal"),
    ("gold", "Au", 79, "transition metal"),
    ("mercury", "Hg", 80, "transition metal"),
    ("lead", "Pb", 82, "post-transition metal"),
    ("radon", "Rn", 86, "noble gas"),
    ("uranium", "U", 92, "actinide"),
    ("arsenic", "As", 33, "metalloid"),
)

# (feature, kind, continent)
FEATURES: Tuple[Tuple[str, str, str], ...] = (
    ("the Nile", "river", "Africa"),
    ("the Amazon", "river", "South America"),
    ("the Yangtze", "river", "Asia"),
    ("the Danube", "river", "Europe"),
    ("the Mississippi", "river", "North America"),
    ("the Volga", "river", "Europe"),
    ("the Ganges", "river", "Asia"),
    ("the Zambezi", "river", "Africa"),
    ("Mount Everest", "mountain", "Asia"),
    ("Mount Kilimanjaro", "mountain", "Africa"),
    ("Mount Fuji", "mountain", "Asia"),
    ("Denali", "mountain", "North America"),
    ("Aconcagua", "mountain", "South America"),
    ("Mont Blanc", "mountain", "Europe"),
    ("the Sahara", "desert", "Africa"),
    ("the Gobi", "desert", "Asia"),
    ("the Atacama", "desert", "South America"),
    ("the Mojave", "desert", "North America"),
    ("the Great Barrier Reef", "coral reef", "Oceania"),
    ("Lake Baikal", "lake", "Asia"),
    ("Lake Victoria", "lake", "Africa"),
    ("Lake Superior", "lake", "North America"),
    ("Victoria Falls", "waterfall", "Africa"),
    ("Angel Falls", "waterfall", "South America"),
    ("the Grand Canyon", "canyon", "North America"),
    ("the Great Rift Valley", "valley", "Africa"),
    ("the Andes", "mountain range", "South America"),
    ("the Himalayas", "mountain range", "Asia"),
    ("the Alps", "mountain range", "Europe"),
    ("the Ural Mountains", "mountain range", "Europe"),
    ("the Serengeti", "national park", "Africa"),
    ("the Amazon rainforest", "rainforest", "South America"),
)

# (achievement, person, country)
ACHIEVEMENTS: Tuple[Tuple[str, str, str], ...] = (
    ("the telephone", "Alexander Graham Bell", "the United States"),
    ("the phonograph", "Thomas Edison", "the United States"),
    ("the World Wide Web", "Tim Berners-Lee", "the United Kingdom"),
    ("movable-type printing in Europe", "Johannes Gutenberg", "Germany"),
    ("the improved steam engine", "James Watt", "the United Kingdom"),
    ("dynamite", "Alfred Nobel", "Sweden"),
    ("pasteurization", "Louis Pasteur", "France"),
    ("penicillin", "Alexander Fleming", "the United Kingdom"),
    ("the polio vaccine", "Jonas Salk", "the United States"),
    ("the electric telegraph code", "Samuel Morse", "the United States"),
    ("long-distance radio transmission", "Guglielmo Marconi", "Italy"),
    ("the first powered aeroplane", "the Wright brothers", "the United States"),
    ("the practical incandescent lamp", "Thomas Edison", "the United States"),
    ("electronic television", "Philo Farnsworth", "the United States"),
    ("the integrated circuit", "Jack Kilby", "the United States"),
    ("the first working laser", "Theodore Maiman", "the United States"),
    ("the analytical engine design", "Charles Babbage", "the United Kingdom"),
    ("the first published computer algorithm", "Ada Lovelace",
     "the United Kingdom"),
    ("the periodic table", "Dmitri Mendeleev", "Russia"),
    ("the discovery of X-rays", "Wilhelm Rontgen", "Germany"),
    ("the discovery of radium and polonium", "Marie Curie", "France"),
    ("the theory of general relativity", "Albert Einstein", "Germany"),
    ("the smallpox vaccine", "Edward Jenner", "the United Kingdom"),
    ("the laws of planetary motion", "Johannes Kepler", "Germany"),
    ("the theory of natural selection", "Charles Darwin",
     "the United Kingdom"),
    ("the first mechanical calculator with carry", "Blaise Pascal", "France"),
)

# (question, answer) in elementary-science style
SCIENCE: Tuple[Tuple[str, str], ...] = (
    ("which gas do plants absorb during photosynthesis", "carbon dioxide"),
    ("what process do green plants use to turn light into chemical energy",
     "photosynthesis"),
    ("what is the freezing point of water at sea level in degrees celsius",
     "zero degrees Celsius"),
    ("what is the boiling point of water at sea level in degrees celsius",
     "100 degrees Celsius"),
    ("which organelle carries out cellular respiration", "the mitochondrion"),
    ("which blood cells carry oxygen", "red blood cells"),
    ("what force keeps the planets in orbit around the sun", "gravity"),
    ("which planet orbits closest to the sun", "Mercury"),
    ("which planet in the solar system is the largest", "Jupiter"),
    ("what is the centre of an atom called", "the nucleus"),
    ("which particle in an atom carries a negative charge", "the electron"),
    ("which particle in an atom carries a positive charge", "the proton"),
    ("which subatomic particle carries no electric charge", "the neutron"),
    ("what is the chemical formula of water", "H2O"),
    ("which state of matter has a fixed volume but no fixed shape", "liquid"),
    ("what is the change from a liquid to a gas called", "evaporation"),
    ("what is the change from a gas to a liquid called", "condensation"),
    ("which rock type forms when magma cools", "igneous rock"),
    ("which instrument measures atmospheric pressure", "a barometer"),
    ("which instrument records earthquakes", "a seismometer"),
    ("which layer of the earth lies directly beneath the crust", "the mantle"),
    ("what do we call animals that eat only plants", "herbivores"),
    ("what do we call an animal that eats both plants and animals",
     "an omnivore"),
    ("what is the loss of water vapour from plant leaves called",
     "transpiration"),
    ("which body system includes the heart and the blood vessels",
     "the circulatory system"),
    ("what is the basic unit of life", "the cell"),
    ("which molecule carries genetic information in most organisms", "DNA"),
    ("how many chromosomes are in a typical human body cell", "46"),
    ("which gas makes up most of the earth's atmosphere", "nitrogen"),
    ("what is the path of one object around another in space called",
     "an orbit"),
    ("what is the si unit of electrical resistance", "the ohm"),
    ("what is the si unit of force", "the newton"),
    ("what is the si unit of energy", "the joule"),
    ("what is the si unit of power", "the watt"),
    ("which type of energy is stored in a stretched spring",
     "elastic potential energy"),
    ("what do we call a substance that speeds up a reaction without being "
     "consumed", "a catalyst"),
    ("what is the ph of a neutral solution at 25 degrees celsius", "7"),
    ("what is the smallest particle of an element that keeps its properties",
     "an atom"),
    ("which process splits a heavy nucleus into lighter nuclei",
     "nuclear fission"),
    ("which process joins light nuclei into a heavier nucleus",
     "nuclear fusion"),
    ("what do we call the variety of life in an ecosystem", "biodiversity"),
    ("which pigment makes plant leaves green", "chlorophyll"),
    ("which organ filters waste from the blood in humans", "the kidney"),
    ("which organ produces insulin", "the pancreas"),
    ("how long does the earth take to complete one orbit of the sun",
     "one year"),
    ("what causes day and night on earth", "the earth's rotation on its axis"),
    ("what do we call a large system of stars bound by gravity", "a galaxy"),
    ("which type of wave needs a medium in order to travel",
     "a mechanical wave"),
    ("what is the bending of light as it passes between two media called",
     "refraction"),
    ("what is the bouncing of light off a surface called", "reflection"),
    ("which simple machine is a sloped surface used to raise a load",
     "an inclined plane"),
    ("what is the force that opposes motion between two surfaces", "friction"),
    ("which process releases energy from sugars in plant and animal cells",
     "respiration"),
    ("which part of a flower produces pollen", "the anther"),
    ("what do we call the push or pull that changes an object's motion",
     "a force"),
    ("which blood vessels carry blood away from the heart", "arteries"),
    ("which blood vessels carry blood back to the heart", "veins"),
    ("which gas do animals release when they breathe out", "carbon dioxide"),
    ("what is the hardest naturally occurring mineral", "diamond"),
    ("which scale measures the hardness of minerals", "the Mohs scale"),
    ("what is molten rock beneath the earth's surface called", "magma"),
    ("what is molten rock that reaches the surface called", "lava"),
    ("which rock type forms from layers of sediment",
     "sedimentary rock"),
    ("which rock type forms under heat and pressure",
     "metamorphic rock"),
    ("what is the solid inner part of the earth's core made mostly of",
     "iron and nickel"),
    ("which natural satellite orbits the earth", "the Moon"),
    ("what is the fourth planet from the sun", "Mars"),
    ("which planet is known for its prominent ring system", "Saturn"),
    ("which planet is closest in size to the earth", "Venus"),
    ("what is a small rocky body orbiting the sun called", "an asteroid"),
    ("what is a body of ice and dust with a tail called", "a comet"),
    ("what do we call a rock that burns up in the atmosphere",
     "a meteor"),
    ("what star is at the centre of our solar system", "the Sun"),
    ("which galaxy contains our solar system", "the Milky Way"),
    ("what unit do astronomers use for the distance light travels in a year",
     "a light year"),
    ("which process changes a solid directly into a gas", "sublimation"),
    ("which process changes a liquid into a solid", "freezing"),
    ("which process changes a solid into a liquid", "melting"),
    ("what is the mixture of two or more metals called", "an alloy"),
    ("what is a substance made of only one kind of atom called",
     "an element"),
    ("what is a substance made of two or more elements chemically joined",
     "a compound"),
    ("what do we call a mixture that looks the same throughout",
     "a homogeneous mixture"),
    ("which part of a solution is present in the greater amount",
     "the solvent"),
    ("what do we call a liquid that dissolves another substance",
     "a solvent"),
    ("which type of charge do protons carry", "positive"),
    ("what flows through a wire in an electric current", "electrons"),
    ("which material allows electric current to pass easily",
     "a conductor"),
    ("which material resists the flow of electric current", "an insulator"),
    ("what is the si unit of electric current", "the ampere"),
    ("what is the si unit of potential difference", "the volt"),
    ("what device stores chemical energy and supplies electric current",
     "a battery"),
    ("which law states that energy cannot be created or destroyed",
     "the law of conservation of energy"),
    ("what kind of energy does a moving object have",
     "kinetic energy"),
    ("what kind of energy does an object have because of its height",
     "gravitational potential energy"),
    ("what is the rate of change of an object's velocity called",
     "acceleration"),
    ("what is the distance travelled divided by the time taken called",
     "speed"),
    ("which quantity has both magnitude and direction", "a vector"),
    ("what is the force of gravity on an object called", "weight"),
    ("what is the amount of matter in an object called", "mass"),
    ("what do we call the upward force a fluid exerts on an object",
     "buoyancy"),
    ("which principle explains why ships float",
     "Archimedes' principle"),
    ("what is the transfer of heat through direct contact called",
     "conduction"),
    ("what is the transfer of heat by moving fluids called", "convection"),
    ("what is the transfer of heat as electromagnetic waves called",
     "radiation"),
    ("which part of a plant anchors it and absorbs water", "the root"),
    ("which part of a plant carries water from the roots to the leaves",
     "the xylem"),
    ("which plant tissue carries sugars from the leaves", "the phloem"),
    ("what do we call the transfer of pollen between flowers",
     "pollination"),
    ("what develops from a fertilised ovule in a flowering plant",
     "a seed"),
    ("what is the first stage of the life cycle of a butterfly", "the egg"),
    ("what do we call an animal with a backbone", "a vertebrate"),
    ("which class of animals is warm blooded and feeds milk to its young",
     "mammals"),
    ("which organ system exchanges gases with the air",
     "the respiratory system"),
    ("which organ controls the nervous system in humans", "the brain"),
    ("how many bones are in the adult human body", "206"),
    ("which tissue connects muscle to bone", "a tendon"),
    ("what do we call the smallest blood vessels", "capillaries"),
    ("which nutrient group provides the body's main energy source",
     "carbohydrates"),
    ("which vitamin does the skin make in sunlight", "vitamin D"),
    ("what do we call organisms that break down dead material",
     "decomposers"),
    ("what do we call the role an organism plays in its habitat",
     "its niche"),
    ("what do we call all the populations living in one area",
     "a community"),
    ("which diagram shows the flow of energy between organisms",
     "a food web"),
    ("which organisms are at the base of most food chains", "producers"),
    ("what do we call a long period of unusually low rainfall",
     "a drought"),
    ("which instrument measures temperature", "a thermometer"),
    ("which instrument measures wind speed", "an anemometer"),
    ("which instrument measures rainfall", "a rain gauge"),
    ("what do we call water moving from the ground into the air",
     "evaporation"),
    ("what do we call the continuous movement of water on earth",
     "the water cycle"),
    ("which gas in the upper atmosphere absorbs ultraviolet light",
     "ozone"),
)

# --- question families -----------------------------------------------------

Family = Callable[[], List[Tuple[str, str]]]


def _capitals() -> List[Tuple[str, str]]:
    out = []
    for country, capital, _ in COUNTRIES:
        out.append((f"what is the capital of {country}", capital))
        out.append((f"which city is the capital city of {country}", capital))
        out.append((f"name the seat of government of {country}", capital))
    return out


def _authors() -> List[Tuple[str, str]]:
    out = []
    for title, author, _ in WORKS:
        out.append((f"who wrote {title}", author))
        out.append((f"who is the author of {title}", author))
        out.append((f"which writer published {title}", author))
    return out


def _symbols() -> List[Tuple[str, str]]:
    out = []
    for name, symbol, _, _ in ELEMENTS:
        out.append((f"what is the chemical symbol for {name}", symbol))
        out.append((f"which symbol denotes the element {name}", symbol))
        out.append((f"give the periodic-table symbol of {name}", symbol))
    return out


def _achievement_people() -> List[Tuple[str, str]]:
    out = []
    for thing, person, _ in ACHIEVEMENTS:
        out.append((f"who is credited with {thing}", person))
        out.append((f"which figure is associated with {thing}", person))
    return out


def _feature_continents() -> List[Tuple[str, str]]:
    out = []
    for feature, kind, continent in FEATURES:
        out.append((f"on which continent is {feature} located", continent))
        out.append((f"which continent contains {feature}", continent))
    return out


def _feature_kinds() -> List[Tuple[str, str]]:
    return [(f"what kind of geographic feature is {f}", k)
            for f, k, _ in FEATURES]


def _atomic_numbers() -> List[Tuple[str, str]]:
    out = []
    for name, _, number, _ in ELEMENTS:
        out.append((f"what is the atomic number of {name}", str(number)))
        out.append((f"which element has atomic number {number}", name))
    return out


def _country_continents() -> List[Tuple[str, str]]:
    out = []
    for country, _, continent in COUNTRIES:
        out.append((f"on which continent is {country}", continent))
        out.append((f"which continent contains {country}", continent))
    return out


def _achievement_countries() -> List[Tuple[str, str]]:
    return [(f"which country is {person} associated with", country)
            for _, person, country in ACHIEVEMENTS]


def _hop_capital_continent() -> List[Tuple[str, str]]:
    out = []
    for country, capital, continent in COUNTRIES:
        out.append((f"which continent contains the country whose capital "
                    f"is {capital}", continent))
        out.append((f"the country governed from {capital} lies on which "
                    f"continent", continent))
    return out


def _hop_author_nationality() -> List[Tuple[str, str]]:
    out = []
    for title, _, nationality in WORKS:
        out.append((f"what was the nationality of the author of {title}",
                    nationality))
        out.append((f"the writer who published {title} held which "
                    f"nationality", nationality))
    return out


def _hop_symbol_category() -> List[Tuple[str, str]]:
    out = []
    for name, symbol, number, category in ELEMENTS:
        out.append((f"which periodic-table category includes the element "
                    f"with symbol {symbol}", category))
        out.append((f"what is the atomic number of the element whose symbol "
                    f"is {symbol}", str(number)))
    return out


def _hop_feature_country() -> List[Tuple[str, str]]:
    out = []
    for feature, kind, continent in FEATURES:
        out.append((f"the {kind} known as {feature} lies on which continent",
                    continent))
    return out


def _hop_achievement_country() -> List[Tuple[str, str]]:
    return [(f"which country is associated with the figure credited with "
             f"{thing}", country)
            for thing, _, country in ACHIEVEMENTS]


def _science() -> List[Tuple[str, str]]:
    out = []
    for question, answer in SCIENCE:
        out.append((question, answer))
        out.append((f"in one word or phrase, {question}", answer))
    return out


def _element_protons() -> List[Tuple[str, str]]:
    out = []
    for name, _, number, category in ELEMENTS:
        out.append((f"how many protons does an atom of {name} have",
                    str(number)))
        out.append((f"which category of the periodic table includes {name}",
                    category))
    return out


def _science_elements() -> List[Tuple[str, str]]:
    return [(f"is {name} classified as a metal, a metalloid or a nonmetal",
             category)
            for name, _, _, category in ELEMENTS]


def _element_electrons() -> List[Tuple[str, str]]:
    out = []
    for name, symbol, number, _ in ELEMENTS:
        out.append((f"how many electrons does a neutral atom of {name} have",
                    str(number)))
        out.append((f"which symbol is used for {name} in a chemical equation",
                    symbol))
    return out


def _capitals_reverse() -> List[Tuple[str, str]]:
    return [(f"which country has {capital} as its capital", country)
            for country, capital, _ in COUNTRIES]


def _symbols_reverse() -> List[Tuple[str, str]]:
    return [(f"which element has the chemical symbol {symbol}", name)
            for name, symbol, _, _ in ELEMENTS]


def _works_by_author() -> List[Tuple[str, str]]:
    return [(f"which work did {author} publish", title)
            for title, author, _ in WORKS]


def _author_nationalities() -> List[Tuple[str, str]]:
    return [(f"what nationality was {author}", nationality)
            for _, author, nationality in WORKS]


def _hop_capital_country_continent() -> List[Tuple[str, str]]:
    return [(f"which country is governed from {capital}, and on which "
             f"continent does it lie", f"{country}, {continent}")
            for country, capital, continent in COUNTRIES]


def _hop_number_symbol() -> List[Tuple[str, str]]:
    return [(f"what is the symbol of the element whose atomic number "
             f"is {number}", symbol)
            for _, symbol, number, _ in ELEMENTS]


def _hop_title_nationality() -> List[Tuple[str, str]]:
    return [(f"the work {title} was written by an author of which "
             f"nationality", nationality)
            for title, _, nationality in WORKS]


def _earth_science_features() -> List[Tuple[str, str]]:
    return [(f"a field study of {feature} would take place on which "
             f"continent", continent)
            for feature, _, continent in FEATURES]


# dataset -> ordered families and id prefix
PLAN: Dict[str, Tuple[str, Sequence[Family]]] = {
    "natural_questions": ("nq", (_capitals, _authors, _symbols,
                                 _achievement_people)),
    "triviaqa": ("tqa", (_country_continents, _atomic_numbers,
                         _feature_continents, _feature_kinds,
                         _achievement_countries, _capitals_reverse,
                         _symbols_reverse, _works_by_author,
                         _author_nationalities)),
    "hotpotqa": ("hqa", (_hop_capital_continent, _hop_author_nationality,
                         _hop_symbol_category, _hop_feature_country,
                         _hop_achievement_country,
                         _hop_capital_country_continent, _hop_number_symbol,
                         _hop_title_nationality)),
    "openbookqa": ("obqa", (_science, _element_protons, _element_electrons,
                            _science_elements, _earth_science_features)),
}


def _items(dataset: str, count: int) -> List[Tuple[str, str]]:
    """The first count unique (query, answer) items for one dataset."""
    _, families = PLAN[dataset]
    pool: List[Tuple[str, str]] = []
    seen = set()
    for family in families:
        for query, answer in family():
            if query in seen:
                continue
            seen.add(query)
            pool.append((query, answer))
    if len(pool) < count:
        raise ValueError(
            f"{dataset}: fact tables yield {len(pool)} unique items, "
            f"{count} requested")
    return pool[:count]


def reference_corpus(size: int) -> List[QAPair]:
    """Build size records, cycling the four datasets in a fixed order."""
    names = list(CORPUS)
    per_dataset = {name: 0 for name in names}
    for index in range(size):
        per_dataset[names[index % len(names)]] += 1

    items = {name: _items(name, count)
             for name, count in per_dataset.items() if count}
    cursors = {name: 0 for name in names}

    pairs: List[QAPair] = []
    for index in range(size):
        name = names[index % len(names)]
        position = cursors[name]
        cursors[name] += 1
        query, answer = items[name][position]
        prefix = PLAN[name][0]
        pairs.append(
            QAPair(
                query=query,
                expected=answer,
                dataset=name,
                kind=CORPUS[name][1],
                pair_id=f"{prefix}-{position:05d}",
            )
        )
    return pairs


def capacity() -> Dict[str, int]:
    """Unique items available per dataset, for the generator's own check."""
    out = {}
    for dataset in PLAN:
        _, families = PLAN[dataset]
        seen = set()
        for family in families:
            seen.update(q for q, _ in family())
        out[dataset] = len(seen)
    return out
