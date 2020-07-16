# External imports
import re
import sys
from typing import Dict, List, Set
from collections import defaultdict
from threading import Thread

from click import echo
from spacy.tokens import Token, Span
from spacy.tokens.doc import Doc
# Hash comparison 4 performance reasons
from spacy.symbols import PERSON, NORP, FACILITY, ORG, GPE, LOC, PRODUCT, EVENT
from spacy.symbols import WORK_OF_ART, LAW, LANGUAGE, DATE, TIME
#
from geopy.geocoders import Nominatim
from geopy import Location
from nameparser.parser import HumanName 
from wikipedia import DisambiguationError
import wikipedia

# Internal imports
try:
    from Analizers.Structures.Span_BinaryTree_tmp import BinaryTree

except ModuleNotFoundError:
    from .Span_BinaryTree_tmp import BinaryTree



Token.set_extension("information", default={})
Span.set_extension("information", default={})
Doc.set_extension("information", default={})

Doc.set_extension("coref_resolved_list", default=[])



## FINAL
GENDER:Dict[str, int] = {
    "femenine" : 1,
    "masculine" : 2,
    "object" : 3
}

GENDER_REVERSE:Dict[int, str] = {
    1 : "femenine",
    2 : "masculine",
    3 : "object"
}

PREFIXES = re.compile("(Mr|St|Mrs|Ms|Dr)[.]?")
INVALID_SURNAMES = re.compile("\Ws")
INVALID_ENTITIES = re.compile("\W.*")

class Knowledge:
    subjects:BinaryTree
    subjects_set:set = set()
    entities:Dict[int, BinaryTree] = defaultdict(
            lambda : BinaryTree(central_point=
                    Knowledge.subjects.root and
                    Knowledge.subjects.root.compare)) # Dict[label, Dict[lower_, Span]]
    verbs:Dict[str, List[Span]] = defaultdict(list)
    nouns:Dict[str, List[Span]] = defaultdict(list)
    
    statements:List[Token] = []

    # Special vars. May move to objects in the future
    # Nouns (People)
    surnames:Dict[str, List[Span]] = defaultdict(list)
    # Nouns (Places)
    localizer:Nominatim = Nominatim(user_agent="firefox")
    locations:Dict[str, Location] = {}

    # Adjectives
    anthonyms:Dict[str, str] = {}


    # Auxiliar
    stdout=sys.stdout
    location_lookup:bool

    def __init__(self, local:bool=False,
                *, entities:Dict[int, Token]=None, verbs:Dict[int, Token]=None, 
                nouns:Dict[int, Token]=None,
                location_lookup:bool=True, 
                binarytree_mid:int=None):
        
        if(local):
            self.entities = {}
            self.verbs = {}
            self.nouns = {}
            # TODO: Make local attr once data struct is done

        # Local because index are relative to doc
        self.subjects = BinaryTree(central_point=binarytree_mid)

        if(entities): self.entities.update(entities)
        if(verbs): self.verbs.update(verbs)
        if(nouns): self.nouns.update(nouns)

        self.location_lookup = location_lookup
    
    def analize_entities(self, doc:Doc):
        for entity in doc.ents:
            if(not INVALID_ENTITIES.match(entity.lower_) and 
                    (manage := ENTITY_LABELS.get(entity.label))):
                self.entities[entity.label].append(entity, compare=entity.start,
                                    multiple_compares=range(entity.start, entity.end))
                check, subj_relation = self.subjects[entity.start]
                if(check):
                    subj_span = subj_relation.values[0]

                    subj_span._.information["entities"].append(entity)
                    entity._.information["reference"] = subj_span

                manage(self, entity)

                

    def coref_gender_extraction(self, main, mention):
        if((mention.end - mention.start) == 1):
            if(info := {
                    "she":GENDER["femenine"], "her":GENDER["femenine"], "herself":GENDER["femenine"],
                    "he":GENDER["masculine"], "his":GENDER["masculine"], "himself":GENDER["masculine"],
                    "it":GENDER["object"], "its":GENDER["object"], "itself":GENDER["object"]
                    }.get(mention.lower_)):
                main._.information["gender"] = info
                return False

        return True


    def manage_person(self, person:Span, *, max_suffix_lookup:int=10):
        # TODO: Check if person is an object by name

        full_name = person.text

        try:
            if(PREFIXES.match(prefix:=next(person.lefts).text)):
                full_name = f"{prefix} {full_name}"
        except StopIteration:
            prefix = None

        suffix_iter = iter(person.doc[person.end:person.end+max_suffix_lookup])

        try:
            if(next(suffix_iter).text == '('):
                suffix = " ("
                for word in suffix_iter:
                    suffix += word.string

                    if(word.text == ')'): break
                else: 
                    suffix = ''

                full_name += suffix
        except StopIteration:
            pass

        parsed_pers = HumanName(full_name)
        pers_list = person.text.split()

        for surname in parsed_pers.surnames_list:
            self.surnames[surname].append(
                person.doc[person.start+pers_list.index(surname.split()[0])]
            )


        


        gender_num = person._.information.get('gender')

        if(not gender_num and "reference" in person._.information):
            gender_num = person._.information["reference"]._.information.get('gender')

        else:
            gender_num = person._.information.get('gender')

        print_sur_list = parsed_pers.surnames_list
        if(prefix or not len(print_sur_list)):
            print_first = parsed_pers.first or 'someone'
        else:
            print_first = parsed_pers.first or print_sur_list.pop(0)

        print(f"[+] Person {parsed_pers.title}{print_first} ({GENDER_REVERSE.get(gender_num)})", end='')
        if(len(print_sur_list)):
            print(f" from the {' family and the '.join(print_sur_list)} family", end='')

        if(len(parsed_pers.nickname_list)):
            print(f" AKA {', and '.join(parsed_pers.nickname_list)}", end='')

        print()



    def manage_location(self, location:Span):
        text = location.text
        if(text and not text in self.locations):
            self.locations[text] = []

            # Threaded for performance reasons
            if(self.location_lookup):
                Thread(target=self.__wikipedia, args=(text,)).start()
                Thread(target=self.__geolocation, args=(text,)).start()

            #print(f"[+] {location} {localizer_result._tuple[1]} {' -> '.join(localizer_result._tuple[0].split(', ')[::-1])}" +
            #        (f" [{wiki_search.url}]" if wiki_search else ''))

    def manage_other(self, other:Span):
        pass


    def __geolocation(self, location:str) -> None:
        localizer_result = self.localizer.geocode(location)

        self.locations[location].insert(0, localizer_result)

        echo(f"[+] {location} {localizer_result._tuple[1]} {' -> '.join(localizer_result._tuple[0].split(', ')[::-1])}",
            file=Knowledge.stdout)

    def __wikipedia(self, query:str) -> None:
        wiki_search = wikipedia.search(query)

        for page in wiki_search:
            try:
                wiki_search = wikipedia.page(page)
                break
            except DisambiguationError:
                pass
        else:
            wiki_search = None

        self.locations[query].insert(1, wiki_search)

        if(wiki_search):
            echo(f"[+] {query} {wiki_search.url}", file=Knowledge.stdout)

ENTITY_LABELS:Dict[int, callable] = {
    PERSON: Knowledge.manage_person, # People, including fictional.
    NORP:lambda _,sp:print(f"NORP - {sp}"), # Nationalities or religious or political groups.
    FACILITY:lambda _,sp:print(f"FACILITY - {sp}"), # Buildings, airports, highways, bridges, etc.
    ORG:lambda _,sp:print(f"ORG - {sp}"), # Companies, agencies, institutions, etc.
    GPE:Knowledge.manage_location, # Countries, cities, states.
    LOC:Knowledge.manage_location, # Non-GPE locations, mountain ranges, bodies of water.
    PRODUCT:lambda _,sp:print(f"PRODUCT - {sp}"), # objects, vehicles, foods, etc. (Not services.)
    EVENT:lambda _,sp:print(f"EVENT - {sp}"), # Named hurricanes, battles, wars, sports events, etc.
    WORK_OF_ART:lambda _,sp:print(f"WORK_OF_ART - {sp}"), # Titles of books, songs, etc.
    LAW:lambda _,sp:print(f"LAW - {sp}"), # Named documents made into laws.
    LANGUAGE:lambda _,sp:print(f"LANGUAGE - {sp}"), # Any named language.
    DATE:lambda _,sp:print(f"DATE - {sp}"), # Absolute or relative dates or periods.
    TIME:lambda _,sp:print(f"TIME - {sp}") # Times smaller than a day.
}